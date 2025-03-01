from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from .models import Job, Favorite, JobCategory, Application, ChatRoom, ChatMessage, RawJob
from users.models import User
from .forms import JobForm
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import JsonResponse
from .spiders.job51 import Job51Spider
from django.views.decorators.http import require_POST
from django.db.models import Q, Count, F, IntegerField, Value, Case, When
from django.db.models.functions import Cast, TruncMonth
from django.utils import timezone
from datetime import timedelta
import json
import re

class JobListView(ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    ordering = ['-post_date']
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 基础筛选：根据用户角色
        if self.request.user.is_authenticated and self.request.user.role == 'employer':
            queryset = queryset.filter(
                Q(audit_status='approved') |
                Q(employer=self.request.user) |
                Q(claim_status='unclaimed', company=self.request.user.company_name)
            )
        else:
            queryset = queryset.filter(audit_status='approved')
        
        # 搜索条件筛选
        q = self.request.GET.get('q')
        category = self.request.GET.get('category')
        location = self.request.GET.get('location')
        salary_range = self.request.GET.get('salary_range')
        
        # 关键词搜索
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(company__icontains=q)
            )
        
        # 类别筛选
        if category:
            try:
                category_obj = JobCategory.objects.get(name=category)
                queryset = queryset.filter(category=category_obj)
            except JobCategory.DoesNotExist:
                pass
        
        # 地区筛选
        if location:
            queryset = queryset.filter(location=location)
        
        # 薪资范围筛选
        if salary_range:
            try:
                # 直接使用salary_range字段进行筛选
                queryset = queryset.filter(salary_range=salary_range)
            except (ValueError, AttributeError):
                pass
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = JobCategory.objects.all()
        context['locations'] = Job.objects.values_list('location', flat=True).distinct()
        return context

class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

class JobCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('jobs:job-list')

    def test_func(self):
        return self.request.user.role == 'employer'

    def handle_no_permission(self):
        messages.error(self.request, '只有招聘方可以发布职位')
        return redirect('jobs:job-list')

    def form_valid(self, form):
        form.instance.employer = self.request.user
        form.instance.audit_status = 'pending'  # 设置为待审核状态
        messages.success(self.request, '职位发布成功，等待管理员审核')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '请检查表单中的错误')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = JobCategory.objects.all()
        return context

# 添加管理员审核列表视图
class JobAuditListView(UserPassesTestMixin, ListView):
    model = Job
    template_name = 'jobs/job_audit_list.html'
    context_object_name = 'jobs'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'admin'
    
    def get_queryset(self):
        return Job.objects.filter(audit_status='pending').order_by('-post_date')

# 添加审核操作视图
@user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')
def audit_job(request, pk):
    if request.method == 'POST':
        job = get_object_or_404(Job, id=pk)
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'approve':
            job.audit_status = 'approved'
            messages.success(request, '职位已通过审核')
        elif action == 'reject':
            job.audit_status = 'rejected'
            messages.warning(request, '职位已被驳回')
        
        job.audit_notes = notes
        job.save()
        
        # 可以在这里添加发送通知给招聘方的逻辑
        
    return redirect('jobs:audit-list')

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    is_favorited = False
    has_applied = False
    can_claim = False
    
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, job=job).exists()
        has_applied = job.applications.filter(user=request.user).exists()
        # 检查是否可以认领职位
        if request.user.role == 'employer' and job.claim_status == 'unclaimed' \
           and request.user.company_name == job.company:
            can_claim = True
    
    context = {
        'job': job,
        'is_favorited': is_favorited,
        'has_applied': has_applied,
        'can_claim': can_claim,
    }
    return render(request, 'jobs/job_detail.html', context)

@login_required
@require_POST
def claim_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    # 验证用户是否为招聘方且公司名称匹配
    if request.user.role != 'employer' or request.user.company_name != job.company:
        messages.error(request, '您没有权限认领此职位')
        return redirect('jobs:job-detail', pk=job_id)
    
    # 验证职位是否可认领
    if job.claim_status != 'unclaimed':
        messages.error(request, '该职位已被认领')
        return redirect('jobs:job-detail', pk=job_id)
    
    # 更新职位状态
    job.claim_status = 'claimed'
    job.employer = request.user
    job.save()
    
    messages.success(request, '职位认领成功')
    return redirect('jobs:job-detail', pk=job_id)

@login_required
def unclaimed_job_list(request):
    """显示待认领的职位列表"""
    if request.user.role != 'employer':
        messages.error(request, '只有招聘方可以访问待认领职位列表')
        return redirect('jobs:job-list')
    
    unclaimed_jobs = Job.objects.filter(
        claim_status='unclaimed',
        company=request.user.company_name
    ).order_by('-post_date')
    
    paginator = Paginator(unclaimed_jobs, 10)
    page = request.GET.get('page')
    jobs = paginator.get_page(page)
    
    return render(request, 'jobs/unclaimed_job_list.html', {'jobs': jobs})

@login_required
def recruiter_home(request):
    if not request.user.role == 'employer':
        messages.error(request, '只有招聘方可以访问此页面')
        return redirect('home')
    
    # 获取待认领的职位
    unclaimed_jobs = Job.objects.filter(
        claim_status='unclaimed',
        company=request.user.company_name
    ).order_by('-created_at')
    
    # 获取已认领的职位
    claimed_jobs = Job.objects.filter(
        employer=request.user
    ).order_by('-claimed_at')
    
    context = {
        'unclaimed_jobs': unclaimed_jobs,
        'claimed_jobs': claimed_jobs
    }
    
    return render(request, 'users/home.html', context)

@login_required
def toggle_favorite(request, pk):
    if request.method == 'POST':
        job = get_object_or_404(Job, id=pk)
        favorite, created = Favorite.objects.get_or_create(user=request.user, job=job)
        
        if not created:
            favorite.delete()
            messages.success(request, '已取消收藏')
        else:
            messages.success(request, '已添加到收藏')
            
        return redirect('jobs:job-detail', pk=pk)

@login_required
def apply_job(request, pk):
    if request.method == 'POST':
        job = get_object_or_404(Job, id=pk)
        
        if job.applications.filter(user=request.user).exists():
            messages.warning(request, '您已经申请过这个职位了')
            return redirect('jobs:job-detail', pk=pk)
        
        Application.objects.create(
            job=job,
            user=request.user,
            status='submitted'
        )
        
        messages.success(request, '申请成功！请等待招聘方查看')
        return redirect('jobs:job-detail', pk=pk)
    
    return redirect('jobs:job-detail', pk=pk)

@login_required
def chat_room(request, job_id, user_id=None):
    job = get_object_or_404(Job, id=job_id)
    
    # 确定聊天对象
    if request.user.role == 'employer':
        if not user_id:
            return redirect('jobs:job-detail', pk=job_id)
        job_seeker = get_object_or_404(User, id=user_id)
        employer = request.user
    else:  # job_seeker
        employer = job.employer
        job_seeker = request.user

    # 获取或创建聊天室
    chat_room, created = ChatRoom.objects.get_or_create(
        job=job,
        job_seeker=job_seeker,
        employer=employer
    )

    # 获取聊天消息
    chat_messages = chat_room.messages.all()

    if request.method == 'POST':
        content = request.POST.get('message')
        attachment = request.FILES.get('attachment')
        
        if content or attachment:
            message = ChatMessage.objects.create(
                room=chat_room,
                sender=request.user,
                content=content or ''
            )
            
            if attachment:
                message.attachment = attachment
                message.attachment_name = attachment.name
                message.save()
                
            if user_id:
                return redirect('jobs:chat-room', job_id=job_id, user_id=user_id)
            return redirect('jobs:chat-room', job_id=job_id)

    return render(request, 'jobs/chat_room.html', {
        'chat_room': chat_room,
        'messages': chat_messages,
        'job': job
    })

@login_required
@require_POST
@login_required
def claim_job(request, job_id):
    if request.method == 'POST':
        job = get_object_or_404(Job, id=job_id)
        
        # 验证用户是否有权限认领
        if request.user.role != 'employer':
            messages.error(request, '只有招聘方可以认领职位')
            return redirect('jobs:job-detail', job_id=job_id)
            
        if job.claim_status != 'unclaimed':
            messages.error(request, '该职位已被认领')
            return redirect('jobs:job-detail', job_id=job_id)
            
        if request.user.company_name != job.company:
            messages.error(request, '只能认领本公司的职位')
            return redirect('jobs:job-detail', job_id=job_id)
        
        # 认领职位
        job.employer = request.user
        job.claim_status = 'claimed'
        job.save()
        
        messages.success(request, '职位认领成功')
        return redirect('jobs:unclaimed-jobs')
    
    return redirect('jobs:job-list')

@login_required
def chat_list(request):
    if request.user.role == 'employer':
        chat_rooms = ChatRoom.objects.filter(employer=request.user)
    else:
        chat_rooms = ChatRoom.objects.filter(job_seeker=request.user)
    
    return render(request, 'jobs/chat_list.html', {
        'chat_rooms': chat_rooms
    })

@login_required
def job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    # 确保只有职位发布者可以查看申请
    if request.user != job.employer:
        messages.error(request, '您没有权限查看此页面')
        return redirect('jobs:job-list')
    
    applications = job.applications.all().select_related('user')
    return render(request, 'jobs/job_applications.html', {
        'job': job,
        'applications': applications
    })

@login_required
def schedule_interview(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    
    # 确保只有招聘方可以安排面试
    if request.user != application.job.employer:
        messages.error(request, '您没有权限执行此操作')
        return redirect('jobs:job-applications', job_id=application.job.id)
    
    if request.method == 'POST':
        interview_date = request.POST.get('interview_date')
        interview_location = request.POST.get('interview_location')
        interview_notes = request.POST.get('interview_notes')
        
        try:
            # 更新申请状态
            application.interview_date = interview_date
            application.interview_location = interview_location
            application.interview_notes = interview_notes
            application.status = 'interview_scheduled'
            application.save()
            
            # 获取或创建聊天室
            chat_room, created = ChatRoom.objects.get_or_create(
                job=application.job,
                job_seeker=application.user,
                employer=request.user
            )
            
            # 发送面试通知消息
            interview_message = (
                f"面试通知：\n"
                f"时间：{interview_date}\n"
                f"地点：{interview_location}\n"
                f"备注：{interview_notes if interview_notes else '无'}"
            )
            
            ChatMessage.objects.create(
                room=chat_room,
                sender=request.user,
                content=interview_message
            )
            
            messages.success(request, '面试已安排，并已通知求职者')
            
        except Exception as e:
            messages.error(request, '安排面试失败，请重试')
            
    return redirect('jobs:job-applications', job_id=application.job.id)

@login_required
def update_application_status(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    
    # 确保只有招聘方可以更新状态
    if request.user != application.job.employer:
        messages.error(request, '您没有权限执行此操作')
        return redirect('jobs:job-applications', job_id=application.job.id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            application.interview_notes = notes
            application.save()
            
            status_display = dict(Application.STATUS_CHOICES)[new_status]
            messages.success(request, f'申请状态已更新为：{status_display}')
            
    return redirect('jobs:job-applications', job_id=application.job.id)

def crawl_jobs(request):
    if request.user.is_staff:  # 只允许管理员操作
        spider = Job51Spider()
        success = spider.search_jobs("Python开发")
        if success:
            messages.success(request, '职位爬取成功')
        else:
            messages.error(request, '职位爬取失败')
    return redirect('jobs:job-list')

def staff_required(function):
    """检查用户是否是管理员的装饰器"""
    actual_decorator = user_passes_test(
        lambda u: u.is_staff,
        login_url=reverse_lazy('users:login'),  # 未登录时重定向到登录页面
        redirect_field_name='next'  # 登录后重定向回原页面
    )
    return actual_decorator(function)

@staff_required
def start_spider(request):
    """启动爬虫进行数据爬取"""
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        pages = int(request.POST.get('pages', 1))
        
        try:
            spider = Job51Spider()
            spider.search_jobs(keyword, pages)
            messages.success(request, f'成功启动爬虫，正在爬取关键词 "{keyword}" 的职位信息')
        except Exception as e:
            messages.error(request, f'启动爬虫失败：{str(e)}')
    
    return redirect('jobs:spider-management')

def spider_management(request):
    """爬虫管理页面"""
    from django.utils import timezone
    from datetime import datetime, time
    from django.core.paginator import Paginator
    
    # 获取今天的开始和结束时间（使用timezone-aware的datetime对象）
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, time.min))
    today_end = timezone.make_aware(datetime.combine(today, time.max))
    
    # 获取所有职位并按状态和创建时间排序
    all_jobs = RawJob.objects.all().annotate(
        status_order=Case(
            When(status='new', then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('status_order', '-created_at')
    
    # 创建分页器，每页显示10条记录
    paginator = Paginator(all_jobs, 10)
    page = request.GET.get('page', 1)
    recent_jobs = paginator.get_page(page)
    
    context = {
        'today_count': RawJob.objects.filter(created_at__range=(today_start, today_end)).count(),
        'pending_count': RawJob.objects.filter(status='new').count(),
        'failed_count': RawJob.objects.filter(status='failed').count(),
        'recent_jobs': recent_jobs
    }
    return render(request, 'jobs/spider_management.html', context)

@staff_required
def raw_job_list(request):
    status = request.GET.get('status')
    source = request.GET.get('source')
    search = request.GET.get('search')
    
    queryset = RawJob.objects.all().annotate(
        status_order=Case(
            When(status='processed', then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('status_order', '-created_at')
    
    if status:
        queryset = queryset.filter(status=status)
    if source:
        queryset = queryset.filter(source=source)
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(company__icontains=search))
    
    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')
    raw_jobs = paginator.get_page(page)
    
    # 获取所有职位类别供批量处理使用
    job_categories = JobCategory.objects.all()
    return render(request, 'jobs/raw_job_list.html', {
        'raw_jobs': raw_jobs,
        'job_categories': job_categories
    })

@login_required
def process_raw_job(request, job_id):
    """处理单个原始职位数据"""
    raw_job = get_object_or_404(RawJob, id=job_id)
    
    if request.method == 'GET':
        categories = JobCategory.objects.all()
        return render(request, 'jobs/process_raw_job.html', {
            'raw_job': raw_job,
            'categories': categories
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            raw_job.title = data.get('title', raw_job.title)
            raw_job.company = data.get('company', raw_job.company)
            raw_job.location = data.get('location', raw_job.location)
            raw_job.salary_range = data.get('salary_range', raw_job.salary_range)
            raw_job.description = data.get('description', raw_job.description)
            raw_job.save()
            return JsonResponse({'success': True, 'message': '职位信息更新成功'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'更新失败：{str(e)}'})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            category_id = data.get('category')
            notes = data.get('notes', '')
            
            # 如果选择了类别，获取对应的类别对象，否则使用默认类别
            if category_id:
                category = get_object_or_404(JobCategory, id=category_id)
            else:
                category, _ = JobCategory.objects.get_or_create(name='其他')
            
            # 创建新职位，使用当前登录用户作为发布者
            Job.objects.create(
                title=raw_job.title,
                company=raw_job.company,
                description=raw_job.description,
                location=raw_job.location,
                salary_range=raw_job.salary_range,
                category=category,
                employer=request.user,
                original_url=raw_job.original_url,
                audit_status='pending'
            )
            
            raw_job.status = 'processed'
            raw_job.save()
            
            return JsonResponse({'success': True, 'message': '职位处理成功'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'处理失败：{str(e)}'})
    
    elif request.method == 'DELETE':
        try:
            raw_job.status = 'ignored'
            raw_job.save()
            return JsonResponse({'success': True, 'message': '职位已忽略'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'操作失败：{str(e)}'})

@login_required
@require_POST
def batch_process_raw_jobs(request):
    """批量处理原始职位数据"""
    try:
        raw_job_ids = request.POST.getlist('raw_job_ids[]')
        if not raw_job_ids:
            return JsonResponse({'status': 'error', 'message': '未选择职位'})
        
        processed_count = 0
        errors = []
        
        for raw_job_id in raw_job_ids:
            try:
                raw_job = RawJob.objects.get(id=raw_job_id)
                
                # 解析原始数据
                job_data = json.loads(raw_job.content) if isinstance(raw_job.content, str) else raw_job.content
                
                # 获取或创建职位类别
                category, _ = JobCategory.objects.get_or_create(
                    name=job_data.get('category', '其他')
                )
                
                # 创建新职位
                Job.objects.create(
                    title=job_data.get('title', ''),
                    company=job_data.get('company', ''),
                    description=job_data.get('description', ''),
                    location=job_data.get('location', ''),
                    salary_range=job_data.get('salary_range', ''),
                    category=category,
                    source=raw_job.source,
                    source_url=job_data.get('url', ''),
                    audit_status='pending'  # 设置为待审核状态
                )
                
                # 更新原始职位状态
                raw_job.status = 'processed'
                raw_job.save()
                
                processed_count += 1
                
            except Exception as e:
                errors.append(f'职位ID {raw_job_id}: {str(e)}')
        
        message = f'成功处理 {processed_count} 个职位'
        if errors:
            message += f', 失败 {len(errors)} 个: {"; ".join(errors)}'
        
        return JsonResponse({
            'status': 'success' if processed_count > 0 else 'error',
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'批量处理失败: {str(e)}'
        })

@require_POST
@user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')
def ignore_raw_job(request, job_id):
    try:
        raw_job = get_object_or_404(RawJob, id=job_id)
        raw_job.status = 'ignored'
        raw_job.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')
def ignore_raw_jobs(request):
    try:
        data = json.loads(request.body)
        job_ids = data.get('ids', [])
        RawJob.objects.filter(id__in=job_ids).update(status='ignored')
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')
def raw_job_details(request, job_id):
    raw_job = get_object_or_404(RawJob, id=job_id)
    html = f"""
    <div class="container">
        <div class="row">
            <div class="col-12">
                <h4>基本信息</h4>
                <table class="table">
                    <tr><th>职位名称</th><td>{raw_job.title}</td></tr>
                    <tr><th>公司名称</th><td>{raw_job.company}</td></tr>
                    <tr><th>工作地点</th><td>{raw_job.location}</td></tr>
                    <tr><th>薪资范围</th><td>{raw_job.salary_range}</td></tr>
                    <tr><th>数据来源</th><td>{raw_job.source}</td></tr>
                    <tr><th>爬取时间</th><td>{raw_job.created_at}</td></tr>
                    <tr><th>处理状态</th><td>{raw_job.get_status_display()}</td></tr>
                </table>
                <h4>职位描述</h4>
                <div class="card">
                    <div class="card-body">{raw_job.description}</div>
                </div>
                <h4>原始数据</h4>
                <div class="card">
                    <div class="card-body">
                        <pre>{json.dumps(raw_job.raw_data, ensure_ascii=False, indent=2)}</pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return JsonResponse({'html': html})

@require_POST
@user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')
def start_spider(request):
    """启动爬虫"""
    keyword = request.POST.get('keyword')
    if not keyword:
        messages.error(request, '请输入关键词')
        return redirect('jobs:spider-management')
        
    try:
        pages = int(request.POST.get('pages', 1))
        if pages < 1 or pages > 50:
            messages.error(request, '页数必须在1-50之间')
            return redirect('jobs:spider-management')
            
        # 启动爬虫
        spider = Job51Spider()
        jobs_data = spider.search_jobs(keyword, pages)
        
        if jobs_data is not None and len(jobs_data) > 0:
            messages.success(request, f'成功爬取 {len(jobs_data)} 条职位信息，关键词："{keyword}"')
        else:
            messages.warning(request, '未找到匹配的职位信息')
            
        return redirect('jobs:spider-management')
            
    except ValueError:
        messages.error(request, '页数必须是整数')
        return redirect('jobs:spider-management')
    except Exception as e:
        messages.error(request, f'爬虫运行出错：{str(e)}')
        return redirect('jobs:spider-management')

@login_required
def market_report(request):
    """市场报告视图函数"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 获取职位分布数据
        job_distribution = Job.objects.filter(audit_status='approved')\
            .values('category__name')\
            .annotate(count=Count('id'))\
            .order_by('-count')
        
        print("职位分布数据:", list(job_distribution))  # 添加调试信息
        
        # 获取薪资分布数据
        salary_ranges = ['0-10k', '10k-20k', '20k-30k', '30k-40k', '40k+']
        salary_counts = [0] * len(salary_ranges)
        
        jobs = Job.objects.filter(audit_status='approved')
        print("已审核职位数量:", jobs.count())  # 添加调试信息
        
        for job in jobs:
            if job.salary_range:
                numbers = [int(n) for n in re.findall(r'\d+', job.salary_range)]
                if len(numbers) >= 2:
                    avg_salary = (numbers[0] + numbers[1]) / 2
                    if avg_salary <= 10:
                        salary_counts[0] += 1
                    elif avg_salary <= 20:
                        salary_counts[1] += 1
                    elif avg_salary <= 30:
                        salary_counts[2] += 1
                    elif avg_salary <= 40:
                        salary_counts[3] += 1
                    else:
                        salary_counts[4] += 1
        
        print("薪资分布数据:", salary_counts)  # 添加调试信息
        
        # 获取地区分布数据
        location_distribution = Job.objects.filter(audit_status='approved')\
            .values('location')\
            .annotate(count=Count('id'))\
            .order_by('-count')[:10]
        
        print("地区分布数据:", list(location_distribution))  # 添加调试信息
        
        # 获取职位趋势数据（最近6个月）
        end_date = timezone.now()
        start_date = end_date - timedelta(days=180)
        
        job_trend = Job.objects.filter(
            audit_status='approved',
            post_date__range=(start_date, end_date)
        ).annotate(
            month=TruncMonth('post_date')
        ).values('month')\
        .annotate(count=Count('id'))\
        .order_by('month')
        
        print("职位趋势数据:", list(job_trend))  # 添加调试信息
        
        # 准备趋势数据
        trend_dates = []
        trend_counts = []
        current_date = start_date
        while current_date <= end_date:
            month_key = current_date.strftime('%Y-%m')
            trend_dates.append(month_key)
            count = next(
                (item['count'] for item in job_trend if item['month'].strftime('%Y-%m') == month_key),
                0
            )
            trend_counts.append(count)
            current_date += timedelta(days=30)
        
        # 准备JSON响应数据
        data = {
            'categoryData': {
                'categories': [item['category__name'] for item in job_distribution],
                'counts': [item['count'] for item in job_distribution]
            },
            'salaryData': {
                'ranges': salary_ranges,
                'counts': salary_counts
            },
            'locationData': {
                'locations': [item['location'] for item in location_distribution],
                'counts': [item['count'] for item in location_distribution]
            },
            'trendData': {
                'dates': trend_dates,
                'counts': trend_counts
            }
        }
        
        return JsonResponse(data)
    
    return render(request, 'jobs/market_report.html')

class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('jobs:job-list')

    def test_func(self):
        job = self.get_object()
        return self.request.user.is_staff or (
            self.request.user.is_authenticated and 
            self.request.user.role == 'employer' and 
            job.employer == self.request.user
        )

    def form_valid(self, form):
        form.instance.employer = self.request.user
        return super().form_valid(form)

@login_required
def favorite_list(request):
    """显示用户收藏的职位列表"""
    favorites = Favorite.objects.filter(user=request.user).select_related('job')
    
    # 分页
    paginator = Paginator(favorites, 10)  # 每页显示10个职位
    page = request.GET.get('page')
    favorites = paginator.get_page(page)
    
    context = {
        'favorites': favorites,
        'page_title': '我的收藏'
    }
    return render(request, 'jobs/favorite_list.html', context)

@login_required
def application_list(request):
    """显示用户的申请列表"""
    if request.user.role == 'employer':
        # 如果是招聘方，显示收到的申请
        applications = Application.objects.filter(
            job__employer=request.user
        ).select_related('job', 'applicant')
    else:
        # 如果是求职者，显示发出的申请
        applications = Application.objects.filter(
            applicant=request.user
        ).select_related('job', 'job__employer')
    
    # 分页
    paginator = Paginator(applications, 10)  # 每页显示10个申请
    page = request.GET.get('page')
    applications = paginator.get_page(page)
    
    context = {
        'applications': applications,
        'page_title': '申请管理',
        'is_employer': request.user.role == 'employer'
    }
    return render(request, 'jobs/application_list.html', context)

@login_required
def application_detail(request, pk):
    """显示申请详情"""
    application = get_object_or_404(Application, pk=pk)
    
    # 检查权限：只有申请人和职位发布者可以查看
    if not (request.user == application.applicant or request.user == application.job.employer):
        messages.error(request, '您没有权限查看此申请')
        return redirect('jobs:application-list')
    
    # 获取聊天记录
    chat_room = ChatRoom.objects.filter(
        Q(application=application) &
        (Q(user1=request.user) | Q(user2=request.user))
    ).first()
    
    messages = []
    if chat_room:
        messages = ChatMessage.objects.filter(room=chat_room).order_by('created_at')
    
    context = {
        'application': application,
        'chat_messages': messages,
        'chat_room': chat_room,
        'is_employer': request.user == application.job.employer,
        'page_title': '申请详情'
    }
    return render(request, 'jobs/application_detail.html', context)

@login_required
def get_messages(request, chat_room_id):
    """获取聊天记录"""
    chat_room = get_object_or_404(ChatRoom, id=chat_room_id)
    
    # 检查权限
    if not (request.user == chat_room.user1 or request.user == chat_room.user2):
        return JsonResponse({
            'status': 'error',
            'message': '您没有权限查看此聊天记录'
        })
    
    # 获取消息
    messages = ChatMessage.objects.filter(room=chat_room).order_by('created_at')
    
    # 格式化消息
    message_list = [{
        'id': msg.id,
        'content': msg.content,
        'sender_id': msg.sender.id,
        'sender_name': msg.sender.username,
        'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for msg in messages]
    
    return JsonResponse({
        'status': 'success',
        'messages': message_list
    })

@login_required
@require_POST
def send_message(request, chat_room_id):
    """发送聊天消息"""
    chat_room = get_object_or_404(ChatRoom, id=chat_room_id)
    
    # 检查权限
    if not (request.user == chat_room.user1 or request.user == chat_room.user2):
        return JsonResponse({
            'status': 'error',
            'message': '您没有权限在此聊天室发送消息'
        })
    
    content = request.POST.get('content')
    if not content:
        return JsonResponse({
            'status': 'error',
            'message': '消息内容不能为空'
        })
    
    # 创建消息
    message = ChatMessage.objects.create(
        room=chat_room,
        sender=request.user,
        content=content
    )
    
    return JsonResponse({
        'status': 'success',
        'message': {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender.id,
            'sender_name': message.sender.username,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })