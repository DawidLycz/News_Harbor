from django.contrib.auth import views
from django.contrib.auth.views import LogoutView, LoginView
from . import views
from django.urls import path

app_name = "newsharborapp"


urlpatterns = [
    path('', views.IndexView.as_view(), name='home'),
    path('articles/', views.ArticleListView.as_view(), name='articles'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article'),
    #### Authorisation ####
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.CustomRegisterView.as_view(), name='register'),
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile'),
    path('profile/<int:pk>/edit', views.UserEditView.as_view(), name='user-edit'),
    path('profile/change-password/', views.UserChangePasswordView.as_view(), name='change-password'),
    #### Work ####
    path('editor-panel', views.EditorPanelView.as_view(), name='editor-panel'),

    path('images/', views.ImageListView.as_view(), name='images'),
    path('images/<int:pk>/', views.ImageDetailView.as_view(), name='image'),
    path('images/<int:pk>/rename', views.ImageRenameView.as_view(), name='image-rename'),
    path('images/<int:pk>/assign', views.ImageAssignView.as_view(), name='image-assign'),
    path('images/create/', views.ImageCreateView.as_view(), name='image-create'),
    path('images/<int:pk>/delete', views.ImageDeleteView.as_view(), name='image-delete'),

    path('articles/select', views.ArticleSelectView.as_view(), name='article-select'),
    path('articles/<int:pk>/edit/', views.ArticleEditView.as_view(), name='article-edit'),
    path('articles/<int:pk>/add-image/', views.ArticleAddImageView.as_view(), name='article-add-image'),
]
