from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import UserRegistrationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from jobs.models import Job, Application
from django.contrib import messages
from .forms import UserProfileForm
from django.db.models import Q
from .models import Profile, User
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 创建用户的 Profile
            Profile.objects.create(
                user=user,
                role=form.cleaned_data.get('role'),
                company_name=form.cleaned_data.get('company_name'),
                skills=form.cleaned_data.get('skills')
            )
            messages.success(request, f'账号 {user.username} 已创建成功！')
            return redirect('users:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = False
    success_url = reverse_lazy('home:index')

# users/views.py
from django.shortcuts import render

def user_home(request):
    if request.user.is_authenticated and request.user.role == 'employer':
        # 获取待认领职位（公司名称匹配且未被认领的职位）
        unclaimed_jobs = Job.objects.filter(
            company=request.user.company_name,
            claim_status='unclaimed'
        ).order_by('-post_date')
        
        # 获取已认领职位
        claimed_jobs = Job.objects.filter(
            employer=request.user,
            claim_status__in=['claimed', 'auto_claimed']
        ).order_by('-post_date')
        
        context = {
            'unclaimed_jobs': unclaimed_jobs,
            'claimed_jobs': claimed_jobs
        }
        return render(request, 'users/home.html', context)
    return render(request, 'users/home.html')  # 或重定向到其他页面

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            # 同时更新Profile模型
            profile = user.profile
            if user.role == 'employer':
                profile.company_intro = form.cleaned_data.get('company_intro', '')
                profile.company_name = form.cleaned_data.get('company_name', user.company_name)
            elif user.role == 'job_seeker':
                profile.skills = form.cleaned_data.get('skills', '')
            profile.save()
            messages.success(request, '个人资料更新成功！')
            return redirect('users:profile')
        else:
            messages.error(request, '请检查表单中的错误！')
    form = UserProfileForm(instance=request.user)
    return render(request, 'users/update_profile.html', {'form': form})

@login_required
def update_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        profile = request.user.profile
        profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, '头像更新成功！')
        return redirect('users:profile')
    return render(request, 'users/update_avatar.html')

@login_required
def update_resume(request):
    if request.method == 'POST' and request.FILES.get('resume'):
        profile = request.user.profile
        profile.resume = request.FILES['resume']
        profile.save()
        messages.success(request, '简历更新成功！')
        return redirect('users:profile')
    return render(request, 'users/update_resume.html')
@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        if old_password and new_password:
            if request.user.check_password(old_password):
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, '密码修改成功！请重新登录。')
                return redirect('users:login')
            else:
                messages.error(request, '原密码不正确！')
        else:
            messages.error(request, '请填写所有必填字段！')
    return render(request, 'users/change_password.html')
@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST['password']
        if request.user.check_password(password):
            request.user.delete()
            messages.success(request, '账号已成功注销。')
            return redirect('home:index')
        else:
            messages.error(request, '密码不正确！')
    return render(request, 'users/delete_account.html')
# users/views.py
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

@login_required
def profile(request):
    user = request.user
    context = {
        'user': user,
    }
    
    if user.role == 'job_seeker':
        # 求职者可以看到收藏的职位和申请的职位
        favorite_jobs = Job.objects.filter(favorite__user=user)
        context['favorite_jobs'] = favorite_jobs
        
        applied_jobs = Job.objects.filter(applications__user=user)
        context['applied_jobs'] = applied_jobs
        
    elif user.role == 'employer':
        # 招聘方可以看到自己发布的职位
        posted_jobs = Job.objects.filter(employer=user).order_by('-post_date')
        # 统计每个职位的申请数量
        for job in posted_jobs:
            job.application_count = job.applications.count()
        context['posted_jobs'] = posted_jobs
    
    return render(request, 'users/profile.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            return redirect('home:index')
        else:
            messages.error(request, '用户名或密码不正确，请重试。')
    
    return render(request, 'users/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, '退出登录成功！')
    return redirect('users:login')

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            # 同时更新Profile模型
            profile = user.profile
            if user.role == 'employer':
                profile.company_intro = form.cleaned_data.get('company_intro', '')
                profile.company_name = form.cleaned_data.get('company_name', user.company_name)
            elif user.role == 'job_seeker':
                profile.skills = form.cleaned_data.get('skills', '')
            profile.save()
            messages.success(request, '个人资料更新成功！')
            return redirect('users:profile')
        else:
            messages.error(request, '请检查表单中的错误！')
    form = UserProfileForm(instance=request.user)
    return render(request, 'users/update_profile.html', {'form': form})

@login_required
def update_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        profile = request.user.profile
        profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, '头像更新成功！')
        return redirect('users:profile')
    return render(request, 'users/update_avatar.html')

@login_required
def update_resume(request):
    if request.method == 'POST' and request.FILES.get('resume'):
        profile = request.user.profile
        profile.resume = request.FILES['resume']
        profile.save()
        messages.success(request, '简历更新成功！')
        return redirect('users:profile')
    return render(request, 'users/update_resume.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        if old_password and new_password:
            if request.user.check_password(old_password):
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, '密码修改成功！请重新登录。')
                return redirect('users:login')
            else:
                messages.error(request, '原密码不正确！')
        else:
            messages.error(request, '请填写所有必填字段！')
    return render(request, 'users/change_password.html')

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST['password']
        if request.user.check_password(password):
            request.user.delete()
            messages.success(request, '账号已成功注销。')
            return redirect('home:index')
        else:
            messages.error(request, '密码不正确！')
    return render(request, 'users/delete_account.html')

@login_required
def user_management(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'users/user_management.html', {'users': users})

@login_required
def change_role(request, user_id):
    if not request.user.is_staff:
        messages.error(request, '您没有权限执行此操作！')
        return redirect('users:user-management')
    
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ['employer', 'job_seeker']:
            user.role = new_role
            user.save()
            messages.success(request, f'用户 {user.username} 的角色已更新为 {new_role}')
        else:
            messages.error(request, '无效的角色类型！')
    return redirect('users:user-management')

@login_required
def delete_user(request, user_id):
    if not request.user.is_staff:
        messages.error(request, '您没有权限执行此操作！')
        return redirect('users:user-management')
    
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'用户 {username} 已被成功删除。')
    return redirect('users:user-management')


