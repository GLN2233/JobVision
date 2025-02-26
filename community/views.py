from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Post, Comment
from .forms import PostForm, CommentForm

def post_list(request):
    category = request.GET.get('category')
    sort = request.GET.get('sort', '-created_at')
    
    posts = Post.objects.all()
    if category and category != 'all':
        posts = posts.filter(category=category)
    
    if sort == 'popular':
        posts = posts.order_by('-views', '-created_at')
    else:
        posts = posts.order_by(sort)
    
    paginator = Paginator(posts, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    return render(request, 'community/post_list.html', {
        'posts': posts,
        'current_category': category,
        'current_sort': sort
    })

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, '帖子发布成功！')
            return redirect('community:post-detail', pk=post.pk)
    else:
        form = PostForm()
    
    return render(request, 'community/post_form.html', {'form': form})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.views += 1
    post.save()
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, '评论发布成功！')
            return redirect('community:post-detail', pk=pk)
    else:
        form = CommentForm()
    
    return render(request, 'community/post_detail.html', {
        'post': post,
        'form': form,
        'comments': post.comments.all()
    })

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user != post.author:
        messages.error(request, '你没有权限编辑这个帖子！')
        return redirect('community:post-detail', pk=pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, '帖子更新成功！')
            return redirect('community:post-detail', pk=pk)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'community/post_form.html', {'form': form, 'is_edit': True})

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user != post.author:
        messages.error(request, '你没有权限删除这个帖子！')
        return redirect('community:post-detail', pk=pk)
    
    post.delete()
    messages.success(request, '帖子已删除！')
    return redirect('community:post-list')

@login_required
def toggle_like(request, pk):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=pk)
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'liked': liked,
            'like_count': post.like_count()
        })
    return JsonResponse({'error': '无效的请求'}, status=400)