from typing import Any
import csv
import json
from io import BytesIO
import base64
import random

from django.db.models import Prefetch
from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import get_object_or_404
from django.views import generic
from django.views.generic.edit import FormView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth.models import User

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, logout, update_session_auth_hash

from django.shortcuts import render, redirect
from django.views import View

from .models import Article, Image, Paragraph, Profile, Comment
from .forms import *

class IndexView(generic.ListView):
    
    model = Article
    template_name = 'newsharborapp/index.html'
    context_object_name = 'articles'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        articles = Article.objects.filter(for_display=True)
        for article in articles:
            photos = article.images.all()
            if photos:
                article.photo = photos[0].photo
            else:
                article.photo = Image.objects.all()[0].photo
        context['articles'] = articles
        return context
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().get(request, *args, **kwargs)
    
class ArticleDetailView(generic.DetailView):

    model = Article
    template_name = 'newsharborapp/article.html'
    context_object_name = 'article.html'


############### Authorisation ##############


class CustomLoginView(LoginView):
    template_name = 'authorisation/login.html'
    form_class = CustomAuthenticationForm
    success_url = reverse_lazy('newsharborapp:home')

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.success_url


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('newsharborapp:home')

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(self.next_page)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    

class CustomRegisterView(generic.CreateView):
    template_name = 'authorisation/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('newsharborapp:home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        Profile(user=user).save()
        return super().form_valid(form)

    def get_success_url(self):
        return self.success_url
    

class ProfileDetailView(generic.DetailView):
    template_name = 'authorisation/user_detail.html'
    model = Profile
    content_object_name = 'profile'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        title = profile.user.groups.all()[0]
        context['title'] = title
        return context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        profile = self.get_object()
        user = profile.user
        req_user = self.request.user
        if user != req_user and not req_user.profile.belong_to('Editor in Chief'):
            return redirect(reverse_lazy('newsharborapp:home'))
        return super().get(request, *args, **kwargs)


class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserEditForm
    template_name = 'authorisation/user_edit.html'
    
    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        if self.request.user != self.get_object():
            return redirect(reverse_lazy('newsharborapp:home'))
        return super().get(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def get_success_url(self) -> str:
        return reverse_lazy('newsharborapp:profile', kwargs={'pk': self.request.user.profile.id})


class UserChangePasswordView(FormView):
    template_name = 'authorisation/user_change_password.html'
    form_class = CustomPasswordChangeForm

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self) -> str:
        return reverse_lazy('newsharborapp:profile', kwargs={'pk': self.request.user.profile.id})

############### Work ##############

class EditorPermissionMixin(PermissionRequiredMixin):
    permission_required = 'newsharborapp.Editor'

    def handle_no_permission(self):
        return redirect('newsharborapp:home') 


class EditorPanelView(generic.TemplateView):

    template_name='newsharborapp/editor_panel.html'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not self.request.user.profile.is_editor:
            return redirect(reverse_lazy('newsharborapp:home'))
        return super().get(request, *args, **kwargs)
    
class ImageListView(generic.ListView):

    model = Image
    template_name = 'newsharborapp/image_list.html'
    context_object_name = 'images'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:

        if not self.request.user.profile.is_editor:
            return redirect(reverse_lazy('newsharborapp:home'))
        return super().get(request, *args, **kwargs)
    
class ImageDetailView(generic.DetailView):

    model = Image
    template_name = 'newsharborapp/image_detail.html'
    context_object_name = 'image'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:

        if not self.request.user.profile.is_editor:
            return redirect(reverse_lazy('newsharborapp:home'))
        return super().get(request, *args, **kwargs)

class ImageRenameView(generic.UpdateView):

    model = Image
    template_name = 'newsharborapp/image_edit.html'
    form_class = ImageRenameForm
    context_object_name = 'image'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['operation'] = 'Rename Image'
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(Image, pk=self.kwargs['pk'])

    def form_valid(self, form):
        form.save()
        self.get_object().id
        return redirect(reverse_lazy('newsharborapp:image', kwargs={'pk': self.get_object().id}))

class ImageAssignView(generic.UpdateView):

    model = Image
    template_name = 'newsharborapp/image_edit.html'
    form_class = ImageAssignForm
    context_object_name = 'image'

    def form_valid(self, form):
        action = self.request.POST.get('action')
        if action == 'unassgin':
            image = self.get_object()
            image.articles.clear()
            image.save()
        else:
            form.save()
        return redirect(reverse_lazy('newsharborapp:image', kwargs={'pk': self.get_object().id}))

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['operation'] = 'Assign Image'
        return context
    
    def get_object(self, queryset=None):
        return get_object_or_404(Image, pk=self.kwargs['pk'])


class ImageCreateView(generic.CreateView):

    model = Image
    form_class = ImageCreateForm
    template_name = 'newsharborapp/image_create.html'
    success_url = reverse_lazy('newsharborapp:images')

class ImageDeleteView(generic.DeleteView):

    model = Image
    template_name = 'newsharborapp/image_delete.html'
    success_url = reverse_lazy('newsharborapp:images')

class ArticleSelectView(generic.ListView):

    model = Article
    template_name = 'newsharborapp/article_select.html'
    context_object_name = 'articles'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        articles = Article.objects.all()
        for article in articles:
            photos = article.images.all()
            if photos:
                article.photo = photos[0].photo
            else:
                article.photo = Image.objects.all()[0].photo
        context['articles'] = articles
        return context


class ArticleEditView(generic.DetailView):

    model = Article
    template_name = 'newsharborapp/article_edit.html'
    context_object_name = 'article'

    def save_all(self, request, *args, **kwargs):
        for paragraph in self.get_object().paragraphs.all():
            paragraph.text = request.POST.get(f'paragraph{paragraph.id}')
            paragraph.save()

    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        if action == "create_lead":
            Paragraph.objects.create(article=self.get_object(), is_lead=True)

        elif action == "create_another":
            self.save_all(request, *args, **kwargs)
            Paragraph.objects.create(article=self.get_object(), is_lead=False)

        elif action == "save_paragraphs":
            self.save_all(request, *args, **kwargs)

        elif "delete_paragraph" in action:
            self.save_all(request, *args, **kwargs)
            pk = action.rsplit("_")[-1]
            Paragraph.objects.get(pk=pk).delete()
        
        elif "delete_image" in action:
            pk = action.rsplit("_")[-1]
            article = self.get_object()
            image = Image.objects.get(pk=pk)
            article.images.remove(image)
        return redirect(request.path)
    
class ArticleAddImageView(generic.DetailView):

    model = Article
    template_name = 'newsharborapp/article_add_image.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['images'] = Image.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        image = Image.objects.get(pk=action)
        article = self.get_object()
        article.images.add(image)
        article.save()
        return redirect(reverse_lazy('newsharborapp:article-edit', kwargs={'pk': self.get_object().id}))

