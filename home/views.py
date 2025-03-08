# home/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from jobs.models import Job, JobCategory
from django.db.models import Count
from django.db.models.functions import Substr

def index(request):
    # 获取所有职位类别
    categories = JobCategory.objects.all()
    
    if request.user.is_authenticated:
        context = {'categories': categories}
        if request.user.role == 'employer':
            # 获取雇主发布的职位
            jobs = Job.objects.filter(employer=request.user).order_by('-post_date')
            context['jobs'] = jobs
        else:
            # 获取最新的已审核通过的职位
            recommended_jobs = Job.objects.filter(audit_status='approved').order_by('-post_date')[:6]
            context['recommended_jobs'] = recommended_jobs
        return render(request, 'home/dashboard.html', context)
    # 未登录用户显示最新职位
    recommended_jobs = Job.objects.filter(audit_status='approved').order_by('-post_date')[:6]
    return render(request, 'home/index.html', {
        'recommended_jobs': recommended_jobs,
        'categories': categories
    })