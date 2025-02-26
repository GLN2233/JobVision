# users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView

app_name = 'users'  # 定义应用名称
urlpatterns = [
    path('register/', views.register, name='register'),  # 正确路径：/users/register/
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('home/', views.user_home, name='user_home'),  # 改为 'home/' 而不是根路径
    path('update-profile/', views.update_profile, name='update-profile'),  # 添加个人资料更新URL
    path('update-avatar/', views.update_avatar, name='update-avatar'),  # 添加头像更新URL
    path('update-resume/', views.update_resume, name='update-resume'),  # 添加简历更新URL
    path('change-password/', views.change_password, name='change-password'),  # 添加密码修改URL
    path('delete-account/', views.delete_account, name='delete-account'),  # 添加账号注销URL
    path('user-management/', views.user_management, name='user-management'),  # 添加用户管理URL
    path('change-role/<int:user_id>/', views.change_role, name='change-role'),  # 添加角色修改URL
    path('delete-user/<int:user_id>/', views.delete_user, name='delete-user'),  # 添加用户删除URL
    
    # 添加密码重置相关的 URL
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             success_url='/users/password_reset/done/'
         ),
         name='password_reset'),
    
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]