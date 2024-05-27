from django.contrib.auth import views
from django.contrib.auth.views import LogoutView, LoginView
from . import views
from django.urls import path

app_name = "newsharborapp"


urlpatterns = [
    path('', views.IndexView.as_view(), name='home'),
    path('about/', views.InfoView.as_view(), name='info'),
    path('api/', views.InfoApiView.as_view(), name='info-api'),
    path('articles/', views.ArticleListView.as_view(), name='articles'),
    path('articles/<int:pk>/', views.ArticleDetailView.as_view(), name='article'),
#### Authorisation ####
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.CustomRegisterView.as_view(), name='register'),
    path('register-editor/', views.CustomRegisterEditorView.as_view(), name='register-editor'),
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile'),
    path('profile/<int:pk>/edit/', views.UserEditView.as_view(), name='user-edit'),
    path('profile/change-password/', views.UserChangePasswordView.as_view(), name='change-password'),
#### Work ####
    path('editor-panel/', views.EditorPanelView.as_view(), name='editor-panel'),

    path('images/', views.ImageListView.as_view(), name='images'),
    path('images/<int:pk>/', views.ImageDetailView.as_view(), name='image'),
    path('images/<int:pk>/rename/', views.ImageRenameView.as_view(), name='image-rename'),
    path('images/<int:pk>/assign/', views.ImageAssignView.as_view(), name='image-assign'),
    path('images/create/', views.ImageCreateView.as_view(), name='image-create'),
    path('images/<int:pk>/delete/', views.ImageDeleteView.as_view(), name='image-delete'),

    path('articles/select/', views.ArticleSelectView.as_view(), name='article-select'),
    path('articles/<int:pk>/edit/', views.ArticleEditView.as_view(), name='article-edit'),
    path('articles/<int:pk>/add-image/', views.ArticleAddImageView.as_view(), name='article-add-image'),

    path('tags/', views.TagListView.as_view(), name='tags'),
    path('tags/<int:pk>/', views.TagDetailView.as_view(), name='tag'),

#### API ####

    path('api/articles/', views.ApiArticleListView.as_view(), name='api-articles'),
    path('api/articles/<int:pk>/', views.ApiArticleDetailView.as_view(), name='api-article'),

    path('api/paragraphs/', views.ApiParagraphListView.as_view(), name='api-paragraphs'),
    path('api/paragraphs/<int:pk>/', views.ApiParagraphDetailView.as_view(), name='api-paragraph'),

    path('api/images/', views.ApiImageListView.as_view(), name='api-images'),
    path('api/images/<int:pk>/', views.ApiImageDetailView.as_view(), name='api-image'),

    path('api/tags/', views.ApiTagListView.as_view(), name='api-tags'),
    path('api/tags/<int:pk>/', views.ApiTagDetailView.as_view(), name='api-tag'),

    path('api/comments/', views.ApiCommentListView.as_view(), name='api-comments'),
    path('api/comments/<int:pk>/', views.ApiCommentDetailView.as_view(), name='api-comment'),
]
