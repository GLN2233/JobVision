from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('chat-list/', views.chat_list, name='chat-list'),
    path('', views.JobListView.as_view(), name='job-list'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('create/', views.JobCreateView.as_view(), name='job-create'),
    path('<int:pk>/update/', views.JobUpdateView.as_view(), name='job-update'),
    path('<int:pk>/favorite/', views.toggle_favorite, name='toggle-favorite'),
    path('favorites/', views.favorite_list, name='favorite-list'),
    path('<int:pk>/apply/', views.apply_job, name='apply-job'),
    path('applications/', views.application_list, name='application-list'),
    path('applications/<int:pk>/', views.application_detail, name='application-detail'),
    path('chat/<int:job_id>/<int:user_id>/', views.chat_room, name='chat-room'),
    path('chat/<int:chat_room_id>/messages/', views.get_messages, name='get-messages'),
    path('chat/<int:chat_room_id>/send/', views.send_message, name='send-message'),
    path('spider-management/', views.spider_management, name='spider-management'),
    path('raw-jobs/', views.raw_job_list, name='raw-job-list'),
    path('raw-jobs/<int:job_id>/details/', views.raw_job_details, name='raw-job-details'),
    path('process-raw-job/<int:job_id>/', views.process_raw_job, name='process-raw-job'),
    path('batch-process-raw-jobs/', views.batch_process_raw_jobs, name='batch-process-raw-jobs'),
    path('ignore-raw-job/<int:job_id>/', views.ignore_raw_job, name='ignore-raw-job'),
    path('ignore-raw-jobs/', views.ignore_raw_jobs, name='ignore-raw-jobs'),
    path('audit/', views.JobAuditListView.as_view(), name='audit-list'),
    path('audit/<int:pk>/', views.audit_job, name='audit-job'),
    path('market-report/', views.market_report, name='market-report'),
    path('unclaimed-jobs/', views.unclaimed_job_list, name='unclaimed-jobs'),
    path('claim/<int:job_id>/', views.claim_job, name='claim-job'),
    path('start-spider/', views.start_spider, name='start-spider'),
    path('<int:job_id>/applications/', views.job_applications, name='job-applications'),
    path('applications/<int:application_id>/schedule-interview/', views.schedule_interview, name='schedule-interview'),
    path('applications/<int:application_id>/update/', views.update_application_status, name='update-application'),
]