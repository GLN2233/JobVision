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

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    upload_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}'s resume"
