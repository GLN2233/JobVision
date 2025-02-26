from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = [
        ('job_seeker', '求职者'),
        ('employer', '招聘方'),
        ('admin', '管理员'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    registration_date = models.DateTimeField(default=timezone.now)

    # 解决 groups 和 user_permissions 的冲突
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True
    )

    def __str__(self):
        return self.username

class Profile(models.Model):
    ROLE_CHOICES = [
        ('job_seeker', '求职者'),
        ('employer', '招聘方'),
        ('admin', '管理员'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='job_seeker')
    company_name = models.CharField(max_length=100, blank=True, null=True)
    company_intro = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    registration_date = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

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

    title = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    salary_range = models.CharField(max_length=50, blank=True, null=True)
    post_date = models.DateTimeField(default=timezone.now)
    employer = models.ForeignKey(User, on_delete=models.CASCADE)
    audit_status = models.CharField(max_length=20, choices=AUDIT_STATUS_CHOICES, default='pending')
    original_url = models.URLField(max_length=255)
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    upload_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}'s resume"

class Application(models.Model):
    STATUS_CHOICES = [
        ('submitted', '已投递'),
        ('viewed', '已查看'),
        ('accepted', '通过'),
        ('rejected', '不通过'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    apply_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')

    class Meta:
        unique_together = ['job', 'user']

    def __str__(self):
        return f"{self.user.username} applied for {self.job.title}"
