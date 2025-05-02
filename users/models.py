from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    """
    自定义用户模型，继承自Django的AbstractUser
    
    扩展了标准用户模型，添加了角色、公司名称、技能等字段
    
    Attributes:
        role (str): 用户角色，可选值为'job_seeker'(求职者)或'employer'(招聘方)
        company_name (str): 公司名称，仅对招聘方用户有效
        skills (str): 用户技能描述
        registration_date (datetime): 用户注册时间
        groups (ManyToManyField): 用户所属的组，使用自定义related_name避免冲突
        user_permissions (ManyToManyField): 用户权限，使用自定义related_name避免冲突
    """
    
    ROLE_CHOICES = [
        ('job_seeker', '求职者'),
        ('employer', '招聘方'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    registration_date = models.DateTimeField(default=timezone.now)

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
        """返回用户名作为对象的字符串表示"""
        return self.username

class Profile(models.Model):
    """
    用户档案模型
    
    存储用户的详细信息，包括角色、公司信息、技能等
    
    Attributes:
        user (OneToOneField): 关联的用户对象
        role (str): 用户角色，可选值为'job_seeker'(求职者)或'employer'(招聘方)
        company_name (str): 公司名称，仅对招聘方用户有效
        company_intro (str): 公司简介
        skills (str): 用户技能描述
        registration_date (datetime): 档案创建时间
        avatar (ImageField): 用户头像
    """
    
    ROLE_CHOICES = [
        ('job_seeker', '求职者'),
        ('employer', '招聘方'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='job_seeker')
    company_name = models.CharField(max_length=100, blank=True, null=True)
    company_intro = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    registration_date = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        """返回用户名和'profile'作为对象的字符串表示"""
        return f"{self.user.username}'s profile"

class Resume(models.Model):
    """
    简历模型
    
    存储用户的简历信息
    
    Attributes:
        user (ForeignKey): 关联的用户对象
        content (str): 简历内容
        upload_date (datetime): 简历上传时间
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    upload_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """返回用户名和'resume'作为对象的字符串表示"""
        return f"{self.user.username}'s resume"
