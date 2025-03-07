# home/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from jobs.models import Job, JobCategory
from django.db.models import Count
from django.db.models.functions import Substr



def index(request):
    if request.user.is_authenticated:
        context = {}
        return render(request, 'home/dashboard.html', context)
    return render(request, 'home/index.html')