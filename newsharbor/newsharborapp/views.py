from typing import Any
import csv
import json
from io import BytesIO
import base64
import random

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


class IndexView(generic.TemplateView):
    
    template_name = "newsharborapp/base.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['test'] = 'view test 123'
        return context
