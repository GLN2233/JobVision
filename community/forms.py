from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入标题'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '请输入内容'}),
            'category': forms.Select(attrs={'class': 'form-select'})
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '写下你的评论...'})
        }
        labels = {
            'content': '评论'
        }