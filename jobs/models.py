from django.db import models
from django.utils import timezone
from users.models import User

class JobCategory(models.Model):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    AUDIT_STATUS_CHOICES = [
        ('pending', '未审核'),
        ('approved', '已审核'),
        ('rejected', '已驳回'),
    ]

    CLAIM_STATUS_CHOICES = [
        ('unclaimed', '未认领'),
        ('claimed', '已认领'),
        ('auto_claimed', '自动认领')
    ]

    title = models.CharField(max_length=100)  # 职位名称
    company = models.CharField(max_length=100)  # 公司名称
    description = models.TextField()  # 职位描述
    location = models.CharField(max_length=100)  # 工作地点
    salary_range = models.CharField(max_length=50, blank=True, null=True)  # 薪资范围
    post_date = models.DateTimeField(default=timezone.now)  # 发布时间
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')  # 发布者
    audit_status = models.CharField(max_length=20, choices=AUDIT_STATUS_CHOICES, default='pending')  # 审核状态
    claim_status = models.CharField(max_length=20, choices=CLAIM_STATUS_CHOICES, default='unclaimed')  # 认领状态
    original_url = models.URLField(max_length=255)  # 原始URL
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE)  # 职位类别

    def __str__(self):
        return self.title

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    content = models.TextField()
    upload_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}'s resume"

class Application(models.Model):
    STATUS_CHOICES = [
        ('submitted', '已申请'),
        ('interview_scheduled', '待面试'),
        ('interviewed', '已面试'),
        ('offer_sent', '面试通过'),
        ('rejected', '不通过'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    apply_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_location = models.CharField(max_length=200, null=True, blank=True)
    interview_notes = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ['job', 'user']

    def __str__(self):
        return f"{self.user.username} applied for {self.job.title}"

class Interview(models.Model):
    RESULT_CHOICES = [
        ('pass', '通过'),
        ('fail', '不通过'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interview_date = models.DateTimeField()
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s interview for {self.job.title}"

class Favorite(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    favorite_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['job', 'user']

    def __str__(self):
        return f"{self.user.username} favorited {self.job.title}"

class Dislike(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dislike_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['job', 'user']

    def __str__(self):
        return f"{self.user.username} disliked {self.job.title}"

class ChatRoom(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    job_seeker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_rooms_as_seeker')
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_rooms_as_employer')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['job', 'job_seeker', 'employer']

    def __str__(self):
        return f"Chat for {self.job.title} between {self.job_seeker.username} and {self.employer.username}"

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/%Y/%m/', null=True, blank=True)
    attachment_name = models.CharField(max_length=255, null=True, blank=True)
    sent_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.sent_at}"

class RawJob(models.Model):
    STATUS_CHOICES = [
        ('new', '新抓取'),
        ('processed', '已处理'),
        ('failed', '处理失败'),
        ('ignored', '已忽略')
    ]

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    salary_range = models.CharField(max_length=100)
    description = models.TextField()
    source = models.CharField(max_length=50)  # 数据来源，如"51job"
    original_url = models.URLField(max_length=255)  # 原始URL
    raw_data = models.JSONField()  # 原始数据
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.company}"
