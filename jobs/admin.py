from django.contrib import admin
from .models import RawJob

@admin.register(RawJob)
class RawJobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'salary_range', 'source', 'status', 'created_at']
    list_filter = ['status', 'source', 'created_at']
    search_fields = ['title', 'company', 'description']
    readonly_fields = ['created_at']
    actions = ['process_selected_jobs']

    def process_selected_jobs(self, request, queryset):
        processed_count = 0
        for raw_job in queryset:
            if raw_job.process():
                processed_count += 1
        
        self.message_user(request, f'成功处理 {processed_count} 个职位')
    process_selected_jobs.short_description = '处理选中的职位'
