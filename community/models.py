from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Post(models.Model):
    """
    社区帖子模型
    
    用于存储用户在社区发布的帖子信息
    
    Attributes:
        title (str): 帖子标题
        content (str): 帖子内容
        author (ForeignKey): 帖子作者
        category (str): 帖子分类，可选值包括'job_seeking'(求职帖)、'experience'(经验分享)等
        created_at (datetime): 帖子发布时间
        updated_at (datetime): 帖子最后更新时间
        likes (ManyToManyField): 点赞该帖子的用户列表
        views (int): 帖子浏览量
    """
    CATEGORY_CHOICES = [
        ('job_seeking', '求职帖'),
        ('experience', '经验分享'),
        ('discussion', '讨论交流'),
        ('other', '其他'),
    ]

    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name='作者')
    category = models.CharField('分类', max_length=20, choices=CATEGORY_CHOICES, default='discussion')
    created_at = models.DateTimeField('发布时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True, verbose_name='点赞')
    views = models.PositiveIntegerField('浏览量', default=0)

    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = '帖子'
        ordering = ['-created_at']

    def __str__(self):
        """返回帖子标题作为对象的字符串表示"""
        return self.title

    def like_count(self):
        """返回帖子的点赞数量"""
        return self.likes.count()

class Comment(models.Model):
    """
    评论模型
    
    用于存储用户对帖子的评论信息
    
    Attributes:
        post (ForeignKey): 评论所属的帖子
        author (ForeignKey): 评论作者
        content (str): 评论内容
        created_at (datetime): 评论发布时间
        likes (ManyToManyField): 点赞该评论的用户列表
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='帖子')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name='作者')
    content = models.TextField('评论内容')
    created_at = models.DateTimeField('发布时间', auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True, verbose_name='点赞')

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']

    def __str__(self):
        """返回评论作者的用户名作为对象的字符串表示"""
        return f'{self.author.username}的评论'

    def like_count(self):
        """返回评论的点赞数量"""
        return self.likes.count()