from django.shortcuts import render, reverse, get_object_or_404
from .models import Post, Comment
from django.apps import apps
from django.contrib.auth.models import User
from django.views.generic import (
    ListView, DetailView, RedirectView,
    CreateView, UpdateView, DeleteView
    )
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.db.models import Q


class Home(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'photo_blog/home.html'
    ordering = ['-date_posted']
    #paginate_by = 4


def search(request):
    queryset_list = Post.objects.all()
    query = request.GET.get('q')
    if query:
        if query.startswith('#'):
            queryset_list = queryset_list.filter(
                Q(caption__icontains=query)
                ).distinct()
        else:
            Profile = apps.get_model('users', 'Profile')
            queryset_list = Profile.objects.filter()
            queryset_list = queryset_list.filter(
                Q(user__username__icontains=query)
                ).distinct()

    context = {
        'posts': queryset_list
    }
    return render(request, "photo_blog/search.html", context)


class ViewProfile(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'photo_blog/user_profile.html'
    context_object_name ='posts'
    ordering = ['-date_posted']

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')


class ViewPost(LoginRequiredMixin, DetailView):
    model = Post


class CreatePost(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['photo', 'caption', 'location']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class UpdatePost(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['caption']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class DeletePost(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    sucess_url = 'photo_blog-home'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


    def get_success_url(self):
        return reverse('photo_blog-home')


class CreateComment(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['text']

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs.get('pk'))
        form.instance.post = post
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        pk = self.kwargs.get('pk')
        return reverse('photo_blog-detail', args={pk: 'pk'})


class DeleteComment(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    sucess_url = '/'

    def test_func(self):
        comment = self.get_object()
        if self.request.user == comment.author:
            return True
        return False

    def get_success_url(self, **kwargs):
        return reverse('photo_blog-home')


class LikePost(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        obj = get_object_or_404(Post, id=self.kwargs.get('pk'))
        user = self.request.user
        if user.is_authenticated:
            if user in obj.likes.all():
                obj.likes.remove(user)
            else:
                obj.likes.add(user)
        return obj.get_absolute_url()


class LikePostAPI(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, slug=None, format=None, pk=None):
        obj = get_object_or_404(Post, id=pk)
        user = self.request.user
        updated = False
        liked = False
        if user.is_authenticated:
            if user in obj.likes.all():
                liked = False
                obj.likes.remove(user)
                like_count = obj.likes.count()
                img = '<a id="imageElement" onclick="toggleLike()"><img src="/media/nav_buttons/unliked.svg" height="17" width="17"></a>'
            else:
                liked = True
                obj.likes.add(user)
                like_count = obj.likes.count()
                img = '<a id="imageElement" onclick="toggleLike()"><img src="/media/nav_buttons/liked.svg" height="17" width="17"></a>'
            updated = True
        data = {
            "updated": updated,
            "liked": liked,
            "like_count": like_count,
            #"img": img
        }
        return Response(data)


class ViewLikes(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'photo_blog/post_likes.html'
    context_object_name ='post'
    ordering = ['-date_posted']

    def get_queryset(self):
        post = get_object_or_404(Post, id=self.kwargs.get('pk'))
        return post
