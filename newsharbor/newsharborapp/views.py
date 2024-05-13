from typing import Any
import datetime

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
from django.utils import timezone

from django.shortcuts import render, redirect

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
    
class ChainLink:
        '''This is spacial class to colect objects Image and Paragraph into one object, and allow to switch their order'''
        def __init__(self, img: Image, paragraph: Paragraph, is_left: bool):

            self.img = img
            self.paragraph = paragraph
            self.is_left = is_left
        def __str__(self) -> str:

            return (self.img, self.paragraph, self.is_left)

class ArticleDetailView(generic.DetailView):

    model = Article
    template_name = 'newsharborapp/article.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        article = self.get_object()
        chain_head, chain_tail = [], []
        paragraphs = article.paragraphs.all()
        if paragraphs:
            context['lead_paragraph'] = paragraphs.filter(is_lead=True)[0]
        images = article.images.all()
        num_paragraphs, num_images = len(paragraphs), len(images)
        if not num_paragraphs:
            chain_tail = ["There is no text for this article yet."]
        else:
            index = 0
            for index, (p, img) in enumerate(zip(paragraphs[1:], images[1:])):
                chain_head.append(ChainLink(img=img, paragraph=p, is_left=index % 2 == 0))
            if num_paragraphs > num_images:
                chain_tail = [p for p in paragraphs[index:]]
            elif num_paragraphs < num_images:
                context['gallery'] = images
        
        article.lead_photo = images[0].photo if images else Image.objects.all()[0].photo
        context['article'] = article
        context['chain_head'] = chain_head
        context['chain_tail'] = chain_tail
        return context


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
        articles = self.get_queryset()
        for article in articles:
            photos = article.images.all()
            if photos:
                article.photo = photos[0].photo
            else:
                article.photo = Image.objects.all()[0].photo
        context['articles'] = articles
        context['editors'] = [profile.user for profile in Profile.objects.filter(is_editor=True)]
        time_periods = Article.objects.first().get_time_periods()
        context['pub_periods'] = [period.capitalize().replace("_", " ") for period in time_periods]
        selected_author = self.request.GET.get('author')
        if selected_author:
            context['selected_author'] = User.objects.get(id = self.request.GET.get('author'))  
        context['selected_display_status'] = self.request.GET.get('display_status', '')
        selected_pub_period = self.request.GET.get('pub_period')
        if selected_pub_period:
            context['selected_pub_period'] = selected_pub_period
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        author_id = self.request.GET.get('author')
        display_status = self.request.GET.get('display_status')
        try:
            pub_period = self.request.GET.get('pub_period').lower().replace(" ","_")
        except AttributeError:
            pub_period = False
        if author_id:
            queryset = queryset.filter(author = author_id)
        if display_status == 'displayed':
            queryset = queryset.filter(for_display=True)
        elif display_status == 'hidden':
            queryset = queryset.filter(for_display=False)
        if pub_period:
            if pub_period == "published_today":
                queryset = queryset.filter(pub_date__date=timezone.now().date())
            if pub_period == "published_last_day":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=1))
            if pub_period == "published_last_week":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=7))
            if pub_period == "published_last_month":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=30))
        return queryset

    
    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        if action == "create_article":
            article = Article.objects.create(title="New article", author=request.user)
            return redirect(reverse_lazy('newsharborapp:article-edit', kwargs={'pk': article.id}))
        return redirect(request.path)


class ArticleEditView(generic.DetailView):

    model = Article
    template_name = 'newsharborapp/article_edit.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['editors'] = [profile.user for profile in Profile.objects.filter(is_editor=True)]
        return context

    def save_all(self, request, *args, **kwargs):
        article = self.get_object()
        article.title = request.POST.get('title')
        article.save()
        for paragraph in self.get_object().paragraphs.all():
            paragraph.title = request.POST.get(f'paragraph_title_{paragraph.id}')
            paragraph.text = request.POST.get(f'paragraph_text_{paragraph.id}')
            paragraph.save()

    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        if action == "create_lead":
            Paragraph.objects.create(title="Lead Paragraph...", article=self.get_object(), is_lead=True)
        elif action == "create_another":
            self.save_all(request, *args, **kwargs)
            Paragraph.objects.create(title="Next Paragraph...", article=self.get_object(), is_lead=False)
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
        elif action == "set_for_display":
            article = self.get_object()
            article.for_display = True
            article.save()
        elif action == "set_hidden":
            article = self.get_object()
            article.for_display = False
            article.save()
        elif action == "save_author":
            author = request.POST.get('author')
            user = User.objects.get(id=author)
            article = self.get_object()
            article.author = user
            article.save()
        elif action == "delete_article":
            article = self.get_object()
            article.delete()
            return redirect(reverse_lazy('newsharborapp:article-select'))
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

