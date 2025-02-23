# home/urls.py
from django.urls import path
from . import views

app_name = 'home'  # 添加应用命名空间

urlpatterns = [
    path('', views.index, name='index'),  # 首页路由
]
