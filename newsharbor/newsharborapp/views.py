from typing import Any
import datetime

from django.db.models.query import QuerySet
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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
from .article_generation import generate_article


class EditorOnlyMixin:
    def get(self, request, *args, **kwargs):
        if not self.request.user.profile.is_editor:
            print ("Acces denied")
            return redirect(reverse_lazy('newsharborapp:home'))
        return super().get(request, *args, **kwargs)

class IndexView(generic.ListView):
    
    model = Article
    template_name = 'newsharborapp/index.html'
    context_object_name = 'articles'


    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:

        context = super().get_context_data(**kwargs)
        articles = Article.objects.filter(for_display=True)[:7]
        for article in articles:
            photos = article.images.all()
            if photos:
                article.photo = photos[0].photo
            else:
                article.photo = Image.objects.all()[0].photo
        context['main_article'] = articles[0]
        context['articles'] = articles[1:]
        return context
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().get(request, *args, **kwargs)
    

class ArticleListView(generic.ListView):
    model = Article
    template_name = 'newsharborapp/article-list.html'
    context_object_name = 'articles'
    paginate_by = 4  

    def get_queryset(self):
        queryset = Article.objects.filter(for_display=True)
        author_id = self.request.GET.get('author')
        pub_period = self.request.GET.get('pub_period', "").lower().replace(" ","_")
        
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        if pub_period:
            if pub_period == "published_today":
                queryset = queryset.filter(pub_date__gte=timezone.now().date())
            if pub_period == "published_last_day":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=1))
            if pub_period == "published_last_week":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=7))
            if pub_period == "published_last_month":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=30))
        
        for article in queryset:
            photos = article.images.all()
            if photos.exists():
                article.photo = photos[0].photo
            else:
                article.photo = Image.objects.first().photo if Image.objects.exists() else None
                
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editors'] = [profile.user for profile in Profile.objects.filter(is_editor=True)]
        context['selected_author'] = self.request.GET.get('author', '')
        context['selected_display_status'] = self.request.GET.get('display_status', '')
        context['selected_pub_period'] = self.request.GET.get('pub_period', '')
        time_periods = Article.objects.first().get_time_periods()
        context['pub_periods'] = [period.capitalize().replace("_", " ") for period in time_periods]
        page = context['page_obj']
        context['articles'] = page
        return context


class ChainLink:
        '''This is spacial class to collect objects Image and Paragraph into one object, and allow to switch their order'''
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
        user = self.request.user
        comments = Comment.objects.filter(article=article)
        chain_head, chain_tail = [], []
        paragraphs = article.paragraphs.all()
        if comments:
            for comment in comments:
                comment.fans_num = len(comment.fans.all())
                comment.haters_num = len(comment.haters.all())
        if paragraphs:
            context['lead_paragraph'] = paragraphs.filter(is_lead=True)[0]
        images = article.images.all()
        num_paragraphs, num_images = len(paragraphs), len(images)
        if not num_paragraphs:
            chain_tail = ["There is no text for this article yet."]
        else:
            index = 1
            for p, img in zip(paragraphs[1:], images[1:]):
                chain_head.append(ChainLink(img=img, paragraph=p, is_left=index % 2 == 0))
                index += 1
            if num_paragraphs > num_images:
                chain_tail = [p for p in paragraphs[index:]]
            elif num_paragraphs < num_images:
                context['gallery'] = images
        
        article.lead_photo = images[0].photo if images else Image.objects.all()[0].photo
        if article.unique_visitors.all():
            context['visits'] = len(article.unique_visitors.all())
        else:
            context['visits'] = 0
        if article.fans.all():
            context['likes'] = len(article.fans.all())
        else:
            context['likes'] = 0
        context['is_fan'] = article.fans.filter(pk=user.pk).exists()
        context['article'] = article
        context['comments'] = comments
        context['chain_head'] = chain_head
        context['chain_tail'] = chain_tail
        return context
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user = self.request.user
        article = self.get_object()
        if user.is_authenticated:
            article.unique_visitors.add(user)
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        article = self.get_object()
        user = self.request.user
        if action == "publish_comment":
            text = request.POST.get('user_comment')
            Comment.objects.create(author=user, article=article, text=text)
        if action == "like_article":
            article.fans.add(user)
        if action == "dislike_article":
            article.fans.remove(user)
        if "like_comment" in action:
            pk = action.rsplit("_", maxsplit=1)[-1]
            comment = Comment.objects.get(pk=pk)
            comment.fans.add(user)
            comment.haters.remove(user)
        if "hate_comment" in action:
            pk = action.rsplit("_", maxsplit=1)[-1]
            comment = Comment.objects.get(pk=pk)
            comment.haters.add(user)
            comment.fans.remove(user)
        if "delete_comment" in action:
            pk = action.rsplit("_", maxsplit=1)[-1]
            comment = Comment.objects.get(pk=pk)
            comment.delete()
            
        return redirect(request.path)


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


class UserEditView(UpdateView):
    model = User
    form_class = CustomUserEditForm
    template_name = 'authorisation/user_edit.html'


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



class EditorPanelView(EditorOnlyMixin, generic.TemplateView):

    template_name='newsharborapp/editor_panel.html'
    

    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        if action == "create_article":
            article = Article.objects.create(title="New article", author=request.user)
            return redirect(reverse_lazy('newsharborapp:article-edit', kwargs={'pk': article.id}))
        return redirect(request.path)


class ImageListView(EditorOnlyMixin, generic.ListView):

    model = Image
    template_name = 'newsharborapp/image_list.html'
    context_object_name = 'images'
    paginate_by = 6 


    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:

        if not self.request.user.profile.is_editor:
            return redirect(reverse_lazy('newsharborapp:home'))
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        page = context['page_obj']
        context['articles'] = page
        return context


class ImageDetailView(EditorOnlyMixin, generic.DetailView):

    model = Image
    template_name = 'newsharborapp/image_detail.html'
    context_object_name = 'image'

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:

        if not self.request.user.profile.is_editor:
            return redirect(reverse_lazy('newsharborapp:home'))
        return super().get(request, *args, **kwargs)


class ImageRenameView(EditorOnlyMixin, generic.UpdateView):

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


class ImageAssignView(EditorOnlyMixin, generic.UpdateView):

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


class ImageCreateView(EditorOnlyMixin, generic.CreateView):

    model = Image
    form_class = ImageCreateForm
    template_name = 'newsharborapp/image_create.html'
    success_url = reverse_lazy('newsharborapp:images')


class ImageDeleteView(EditorOnlyMixin, generic.DeleteView):

    model = Image
    template_name = 'newsharborapp/image_delete.html'
    success_url = reverse_lazy('newsharborapp:images')


class ArticleSelectView(EditorOnlyMixin, generic.ListView):

    model = Article
    template_name = 'newsharborapp/article_select.html'
    context_object_name = 'articles'
    paginate_by = 6  


    def get_queryset(self):
        queryset = super().get_queryset()
        author_id = self.request.GET.get('author', '')
        display_status = self.request.GET.get('display_status')
        pub_period = self.request.GET.get('pub_period', "").lower().replace(" ","_")

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
        for article in queryset:
            photos = article.images.all()
            if photos:
                article.photo = photos[0].photo
            else:
                article.photo = Image.objects.all()[0].photo
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        articles = self.get_queryset()

        context['editors'] = [profile.user for profile in Profile.objects.filter(is_editor=True)]
        time_periods = Article.objects.first().get_time_periods()
        context['pub_periods'] = [period.capitalize().replace("_", " ") for period in time_periods]
        context['selected_author'] = self.request.GET.get('author', '')
        context['selected_display_status'] = self.request.GET.get('display_status', '')
        context['selected_pub_period'] = self.request.GET.get('pub_period', '')
        page = context['page_obj']
        context['articles'] = page
        return context    
    

    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        if action == "create_article":
            article = Article.objects.create(title="New article", author=request.user)
            return redirect(reverse_lazy('newsharborapp:article-edit', kwargs={'pk': article.id}))
        return redirect(request.path)


class ArticleEditView(EditorOnlyMixin, generic.DetailView):

    model = Article
    template_name = 'newsharborapp/article_edit.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        article = self.get_object()
        context['editors'] = [profile.user for profile in Profile.objects.filter(is_editor=True)]
        context['num_paragraphs'] = len(article.paragraphs.all())
        context['num_images'] = len(article.images.all())
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
        article = self.get_object()
        if action == "create_lead":
            Paragraph.objects.create(title="Lead Paragraph...", article=article, is_lead=True)
        elif action == "create_another":
            self.save_all(request, *args, **kwargs)
            Paragraph.objects.create(title="Next Paragraph...", article=article, is_lead=False)
        elif action == "save_paragraphs":
            self.save_all(request, *args, **kwargs)
        elif "delete_paragraph" in action:
            self.save_all(request, *args, **kwargs)
            pk = action.rsplit("_")[-1]
            Paragraph.objects.get(pk=pk).delete()        
        elif "delete_image" in action:
            pk = action.rsplit("_")[-1]
            image = Image.objects.get(pk=pk)
            article.images.remove(image)
        elif action == "set_for_display":
            article.for_display = True
            article.save()
        elif action == "set_hidden":
            article.for_display = False
            article.save()
        elif action == "save_author":
            author = request.POST.get('author')
            user = User.objects.get(id=author)
            article.author = user
            article.save()
        elif action == "delete_article":
            article.delete()
            return redirect(reverse_lazy('newsharborapp:article-select'))
        elif action == "generate_article":
            print ('genereate')
            topic = request.POST.get('ai_ariticle_topic')
            Paragraph.objects.filter(article=article).delete()
            article_dict = generate_article(topic)
            paragraphs_num = (len(article_dict) - 1) // 2
            article.title = article_dict.get('title', 'No title')
            for num in range(paragraphs_num):
                num += 1
                title = article_dict.get(f"paragraph{num}_title", f"paragraph {num} title")
                text = article_dict.get(f"paragraph{num}_text", f"paragraph {num} text")
                Paragraph.objects.create(article=article, title=title, text=text, is_lead=num==1)
            article.save()
        return redirect(request.path)


class ArticleAddImageView(EditorOnlyMixin, generic.DetailView):

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

