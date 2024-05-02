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
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.views import View

from .models import Article, Image, Paragraph

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
        return super().get(request, *args, **kwargs)
    