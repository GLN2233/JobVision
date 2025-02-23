# home/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from jobs.models import Job

def index(request):
    if request.user.is_authenticated:
        context = {}
        if request.user.role == 'employer':
            # 获取招聘方发布的职位
            jobs = Job.objects.filter(employer=request.user).order_by('-post_date')[:5]
            context['jobs'] = jobs
        else:
            # 获取推荐职位（这里简单展示最新的5个职位）
            recommended_jobs = Job.objects.filter(audit_status='approved').order_by('-post_date')[:5]
            context['recommended_jobs'] = recommended_jobs
        
        return render(request, 'home/dashboard.html', context)
    return render(request, 'home/index.html')