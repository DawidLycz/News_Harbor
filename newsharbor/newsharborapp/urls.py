from django.contrib.auth import views
from django.contrib.auth.views import LogoutView
from . import views
from django.urls import path

app_name = "newsharborapp"


urlpatterns = [
    path('', views.IndexView.as_view(), name='home'),
]