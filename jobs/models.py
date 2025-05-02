from django.db import models
from django.utils import timezone
from users.models import User

class JobCategory(models.Model):
    """
    职位类别模型
    
    用于对职位进行分类管理
    
    Attributes:
        name (str): 类别名称
        parent (ForeignKey): 父类别，允许创建层级分类结构
    """
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        """返回类别名称作为对象的字符串表示"""
        return self.name

class Job(models.Model):
    """
    职位模型
    
    存储职位相关信息，包括职位描述、薪资、地点等
    
    Attributes:
        title (str): 职位名称
        company (str): 公司名称
        description (str): 职位描述
        location (str): 工作地点
        salary_range (str): 薪资范围
        post_date (datetime): 发布时间
        employer (ForeignKey): 发布该职位的雇主
        audit_status (str): 审核状态，可选值为'pending'(未审核)、'approved'(已审核)、'rejected'(已驳回)
        claim_status (str): 认领状态，可选值为'unclaimed'(未认领)、'claimed'(已认领)、'auto_claimed'(自动认领)
        original_url (str): 职位原始URL
        category (ForeignKey): 职位所属类别
        raw_data (JSONField): 职位标签信息，存储为JSON格式
    """

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

    title = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    salary_range = models.CharField(max_length=50, blank=True, null=True)
    post_date = models.DateTimeField(default=timezone.now)
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    audit_status = models.CharField(max_length=20, choices=AUDIT_STATUS_CHOICES, default='pending')
    claim_status = models.CharField(max_length=20, choices=CLAIM_STATUS_CHOICES, default='unclaimed')
    original_url = models.URLField(max_length=255)
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE)
    raw_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        """返回职位名称作为对象的字符串表示"""
        return self.title

class Resume(models.Model):
    """
    简历模型
    
    存储用户的简历信息
    
    Attributes:
        user (ForeignKey): 关联的用户对象
        content (str): 简历内容
        upload_date (datetime): 简历上传时间
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    content = models.TextField()
    upload_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        """返回用户名和'resume'作为对象的字符串表示"""
        return f"{self.user.username}'s resume"

class Application(models.Model):
    """
    职位申请模型
    
    记录用户的职位申请信息和面试进度
    
    Attributes:
        job (ForeignKey): 申请的职位
        user (ForeignKey): 申请人
        apply_date (datetime): 申请时间
        status (str): 申请状态，可选值包括'submitted'(已申请)、'interview_scheduled'(待面试)等
        interview_date (datetime): 面试时间
        interview_location (str): 面试地点
        interview_notes (str): 面试备注
    """
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
        """返回申请人和职位名称作为对象的字符串表示"""
        return f"{self.user.username} applied for {self.job.title}"

class Interview(models.Model):
    """
    面试模型
    
    记录面试相关信息
    
    Attributes:
        job (ForeignKey): 面试的职位
        user (ForeignKey): 面试者
        interview_date (datetime): 面试时间
        result (str): 面试结果，可选值为'pass'(通过)或'fail'(不通过)
    """
    RESULT_CHOICES = [
        ('pass', '通过'),
        ('fail', '不通过'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    interview_date = models.DateTimeField()
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, null=True, blank=True)

    def __str__(self):
        """返回面试者和职位名称作为对象的字符串表示"""
        return f"{self.user.username}'s interview for {self.job.title}"

class Favorite(models.Model):
    """
    收藏模型
    
    记录用户收藏的职位
    
    Attributes:
        job (ForeignKey): 收藏的职位
        user (ForeignKey): 收藏的用户
        favorite_date (datetime): 收藏时间
    """
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    favorite_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['job', 'user']

    def __str__(self):
        """返回用户名和收藏的职位名称作为对象的字符串表示"""
        return f"{self.user.username} favorited {self.job.title}"

class Dislike(models.Model):
    """
    不感兴趣模型
    
    记录用户标记为不感兴趣的职位
    
    Attributes:
        job (ForeignKey): 不感兴趣的职位
        user (ForeignKey): 标记的用户
        dislike_date (datetime): 标记时间
    """
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
    processed_at = models.DateTimeField(null=True, blank=True)

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
    processed_at = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, null=True, blank=True)  # 职位类别

    def __str__(self):
        return f"{self.title} - {self.company}"
