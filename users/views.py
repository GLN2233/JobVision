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
from django.contrib.auth.models import User
from .models import Profile

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

def logout_view(request):
    logout(request)
    messages.success(request, '您已成功退出登录！')
    return redirect('home:index')


