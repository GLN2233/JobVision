from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.post_list, name='post-list'),
    path('post/create/', views.post_create, name='post-create'),
    path('post/<int:pk>/', views.post_detail, name='post-detail'),
    path('post/<int:pk>/edit/', views.post_edit, name='post-edit'),
    path('post/<int:pk>/delete/', views.post_delete, name='post-delete'),
    path('post/<int:pk>/like/', views.toggle_like, name='toggle-like'),
]