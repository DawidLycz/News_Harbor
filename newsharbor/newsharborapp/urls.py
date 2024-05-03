from django.contrib.auth import views
from django.contrib.auth.views import LogoutView, LoginView
from . import views
from django.urls import path

app_name = "newsharborapp"


urlpatterns = [
    path('', views.IndexView.as_view(), name='home'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout')
]