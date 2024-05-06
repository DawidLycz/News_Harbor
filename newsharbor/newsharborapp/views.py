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

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, logout, update_session_auth_hash

from django.shortcuts import render, redirect
from django.views import View

from .models import Article, Image, Paragraph, Profile, Comment
from .forms import *

class IndexView(generic.ListView):
    
    model = Article
    template_name = "newsharborapp/index.html"
    context_object_name = 'articles'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        articles = Article.objects.filter(for_display=True)
        for article in articles:
            photos = article.images.filter(is_lead=True)
            if photos:
                article.photo = photos[0].photo
            else:
                article.photo = Image.objects.all()[0].photo
        context['articles'] = articles
        return context
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        print (request)
        return super().get(request, *args, **kwargs)
    
class ArticleDetailView(generic.DetailView):

    model = Article
    template_name = "newsharborapp/article.html"
    context_object_name = 'article.html'


############### Authorisation ##############


class CustomLoginView(LoginView):
    template_name = 'login.html'
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
    template_name = 'register.html'
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
    template_name = 'user_detail.html'
    model = Profile
    content_object_name = "profile"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        title = profile.user.groups.all()[0]
        print (title)
        context["title"] = title
        return context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        profile = self.get_object()
        user = profile.user
        req_user = self.request.user
        if user != req_user and not req_user.profile.belong_to("Editor in Chief"):
            print("nope")
            return redirect(reverse_lazy('newsharborapp:home'))
        return super().get(request, *args, **kwargs)


class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserEditForm
    template_name = 'user_edit.html'
    
    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        if self.request.user != self.get_object():
            return redirect(reverse_lazy('newsharborapp:home'))
        return super().get(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def get_success_url(self) -> str:
        return reverse_lazy('newsharborapp:profile', kwargs={'pk': self.request.user.profile.id})


class UserChangePasswordView(FormView):
    template_name = 'user_change_password.html'
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