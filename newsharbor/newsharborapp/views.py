import datetime
from string import digits, punctuation
from typing import Any

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.generic.edit import FormView, UpdateView

from rest_framework import status, mixins, generics, permissions, renderers, viewsets, filters
from rest_framework import generics as drfgenerics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework.parsers import JSONParser
from rest_framework.reverse import reverse as drf_reverse

from .article_generation import generate_article
from .forms import *
from .models import Article, Comment, Image, Paragraph, Profile, Tag
from .serializers import *
from .permissions import *
from .utils import *


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
                article.photo = Image.objects.filter(name='default')[0].photo
        if articles.exists():
            context['main_article'] = articles[0]
            context['articles'] = articles[1:]
        else:
            context['articles'] = None
        return context


class InfoView(generic.TemplateView):
    template_name = "newsharborapp/site_info.html"


class InfoApiView(generic.TemplateView):
    template_name = "newsharborapp/api_info.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            context['full_info'] = user.profile.is_editor
        return context
    

class ArticleListView(generic.ListView):
    model = Article
    template_name = 'newsharborapp/article-list.html'
    context_object_name = 'articles'
    paginate_by = 4
    
    def get_queryset(self):
        queryset = Article.objects.filter(for_display=True)
        author_id = self.request.GET.get('author', "")
        pub_period = self.request.GET.get('pub_period', "").lower().replace(" ","_")
        category = self.request.GET.get('category', '')
        search_phrase = self.request.GET.get('search', '')
        if search_phrase:
            search_words = clean_search_phrase(search_phrase)
            tags = Tag.objects.filter(name__in=search_words)
            if tags.exists():
                queryset = queryset.filter(tags__in=tags)
            else:
                queryset = Article.objects.none()
        if category:
            tag = Tag.objects.filter(name=category).first()
            queryset = queryset.filter(tags__id=tag.id)

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
        queryset = queryset.distinct()
        for article in queryset:
            photos = article.images.all()
            if photos.exists():
                article.photo = photos[0].photo
            else:
                article.photo = Image.objects.filter(name='default')[0].photo
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['articles_num'] = self.get_queryset().count()
        context['editors'] = [profile.user for profile in Profile.objects.filter(is_editor=True)]
        context['selected_author'] = self.request.GET.get('author', '')
        context['selected_display_status'] = self.request.GET.get('display_status', '')
        context['selected_pub_period'] = self.request.GET.get('pub_period', '')
        time_periods = Article.objects.first().get_time_periods()
        context['pub_periods'] = [period.capitalize().replace("_", " ") for period in time_periods]
        context['categories'] = Tag.objects.filter(major=True)
        context['selected_category'] = self.request.GET.get('category', '')
        context['searched_phrase'] = self.request.GET.get('search', '')
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
        
        article.lead_photo = images[0].photo if images else Image.objects.filter(name='default')[0].photo
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
        article = self.get_object()
        user = self.request.user
        if user.is_authenticated:
            article.unique_visitors.add(self.request.user)
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
    
    
class CustomRegisterEditorView(EditorOnlyMixin, generic.CreateView):
    template_name = 'authorisation/register-editor.html'
    form_class = CustomEditorCreationForm
    success_url = reverse_lazy('newsharborapp:home')

    def form_valid(self, form):
        user = form.save()
        is_editor_in_chief = form.cleaned_data.get('is_editor_in_chief', False)
        is_editor = form.cleaned_data.get('is_editor', False)
        reader_group = Group.objects.get(name='Reader')
        editor_group = Group.objects.get(name='Editor')
        editor_in_chief_group = Group.objects.get(name='Editor in Chief')
        if is_editor_in_chief:
            user.groups.add(editor_group)
            user.groups.add(editor_in_chief_group)
        elif is_editor:
            editor_group = Group.objects.get(name='Editor')
            user.groups.add(editor_group)
        user.groups.add(reader_group)
        Profile.objects.create(user=user, is_editor_in_chief=is_editor_in_chief, is_editor=is_editor)
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
        if profile.is_editor_in_chief:
            title = "Editor in Chief"
        elif profile.is_editor:
            title = "Editor"
        else:
            title = "Reader"
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


############### Work ##########################



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

    
    def get_queryset(self):
        queryset = Image.objects.all()
        article = self.request.GET.get('article')
        pub_period = self.request.GET.get('pub_period', "").lower().replace(" ","_")
        category = self.request.GET.get('category', '')
        search_phrase = self.request.GET.get('search', '')
        if search_phrase:
            search_words = clean_search_phrase(search_phrase)
            tags = Tag.objects.filter(name__in=search_words)
            if tags.exists():
                queryset = queryset.filter(tags__in=tags)
            else:
                queryset = Image.objects.none()
        if category:
            tag = Tag.objects.filter(name=category).first()
            queryset = queryset.filter(tags__id=tag.id)

        if article:
            queryset = queryset.filter(articles=article)
        if pub_period:
            if pub_period == "published_today":
                queryset = queryset.filter(pub_date__gte=timezone.now().date())
            if pub_period == "published_last_day":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=1))
            if pub_period == "published_last_week":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=7))
            if pub_period == "published_last_month":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=30))
        queryset = queryset.distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['articles'] = Article.objects.all()
        context['images_num'] = self.get_queryset().count()
        context['selected_article'] = self.request.GET.get('article', '')
        context['selected_pub_period'] = self.request.GET.get('pub_period', '')
        time_periods = Article.objects.first().get_time_periods()
        context['pub_periods'] = [period.capitalize().replace("_", " ") for period in time_periods]
        context['categories'] = Tag.objects.filter(major=True)
        context['selected_category'] = self.request.GET.get('category', '')
        context['placeholder'] = self.request.GET.get('search', 'Search')
        context['searched_phrase'] = self.request.GET.get('search', '')

        page = context['page_obj']
        context['images'] = page
        return context


class ImageDetailView(EditorOnlyMixin, generic.DetailView):

    model = Image
    template_name = 'newsharborapp/image_detail.html'
    context_object_name = 'image'

    
    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        image = self.get_object()
        if "delete_tag" in action:
            pk = action.rsplit("_")[-1]
            tag = Tag.objects.get(pk=pk)
            tag.images.remove(image)
        elif action == "add_tag":
            tags = request.POST.get(f'tag_name').split(",")
            if tags:
                for tag_name in tags:
                    tag_name = tag_name.strip().capitalize()
                    tag = Tag.objects.filter(name=tag_name).first()
                    if not tag:
                        tag = Tag.objects.create(name=tag_name)
                        tag.save()
                    tag.images.add(image)
        return redirect(request.path)


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
    
    def form_valid(self, form):
        image_instance = form.save(commit=False)
        name = image_instance.photo.name
        if "." in name:
            name = name.rsplit(".", 1)[0]
        image_instance.name = name
        image_instance.save()
        return super().form_valid(form)

class ImageDeleteView(EditorOnlyMixin, generic.DeleteView):

    model = Image
    template_name = 'newsharborapp/image_delete.html'
    success_url = reverse_lazy('newsharborapp:images')


class ArticleSelectView(EditorOnlyMixin, generic.ListView):

    model = Article
    template_name = 'newsharborapp/article_select.html'
    context_object_name = 'articles'
    paginate_by = 4


    def get_queryset(self):
        queryset = Article.objects.all()
        author_id = self.request.GET.get('author', '')
        display_status = self.request.GET.get('display_status')
        pub_period = self.request.GET.get('pub_period', "").lower().replace(" ","_")
        category = self.request.GET.get('category', '')
        search_phrase = self.request.GET.get('search', '')
        if search_phrase:
            search_words = clean_search_phrase(search_phrase)
            tags = Tag.objects.filter(name__in=search_words)
            if tags.exists():
                queryset = queryset.filter(tags__in=tags)
            else:
                queryset = Article.objects.none()
        if category:
            tag = Tag.objects.filter(name=category).first()
            queryset = queryset.filter(tags__id=tag.id)

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
        queryset = queryset.distinct()
        for article in queryset:
            photos = article.images.all()
            if photos:
                article.photo = photos[0].photo
            else:
                article.photo = Image.objects.filter(name='default')[0].photo
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['editors'] = [profile.user for profile in Profile.objects.filter(is_editor=True)]
        time_periods = Article().time_periods
        context['articles_num'] = self.get_queryset().count()
        context['pub_periods'] = [period.capitalize().replace("_", " ") for period in time_periods]
        context['selected_author'] = self.request.GET.get('author', '')
        context['selected_display_status'] = self.request.GET.get('display_status', '')
        context['selected_pub_period'] = self.request.GET.get('pub_period', '')
        context['categories'] = Tag.objects.filter(major=True)
        context['selected_category'] = self.request.GET.get('category', '')
        context['searched_phrase'] = self.request.GET.get('search', '')
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
        elif "delete_tag" in action:
            pk = action.rsplit("_")[-1]
            tag = Tag.objects.get(pk=pk)
            tag.articles.remove(article)
        elif action == "add_tag":
            tags = request.POST.get(f'tag_name').split(",")
            if tags:
                for tag_name in tags:
                    tag_name = tag_name.strip().capitalize()
                    tag = Tag.objects.filter(name=tag_name).first()
                    if not tag:
                        tag = Tag.objects.create(name=tag_name)
                        tag.save()
                    tag.articles.add(article)
        return redirect(request.path)


class ArticleAddImageView(EditorOnlyMixin, generic.DetailView):
    model = Article
    template_name = 'newsharborapp/article_add_image.html'
    context_object_name = 'article'
    paginate_by = 6


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Image.objects.all()
        article = self.request.GET.get('article')
        pub_period = self.request.GET.get('pub_period', "").lower().replace(" ","_")
        category = self.request.GET.get('category', '')
        search_phrase = self.request.GET.get('search', '')
        if search_phrase:
            search_words = clean_search_phrase(search_phrase)
            tags = Tag.objects.filter(name__in=search_words)
            if tags.exists():
                queryset = queryset.filter(tags__in=tags)
            else:
                queryset = Image.objects.none()
        if category:
            tag = Tag.objects.filter(name=category).first()
            queryset = queryset.filter(tags__id=tag.id)

        if article:
            queryset = queryset.filter(articles=article)
        if pub_period:
            if pub_period == "published_today":
                queryset = queryset.filter(pub_date__gte=timezone.now().date())
            if pub_period == "published_last_day":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=1))
            if pub_period == "published_last_week":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=7))
            if pub_period == "published_last_month":
                queryset = queryset.filter(pub_date__gte=timezone.now() - datetime.timedelta(days=30))
        queryset = queryset.distinct()

        paginator = Paginator(queryset, self.paginate_by)
        
        page = self.request.GET.get('page')
        images = paginator.get_page(page)
        
        context['images'] = images
        context['images_num'] = queryset.count()
        context['articles'] = Article.objects.all()
        context['selected_article'] = self.request.GET.get('article', '')
        context['selected_pub_period'] = self.request.GET.get('pub_period', '')
        time_periods = Article.objects.first().get_time_periods()
        context['pub_periods'] = [period.capitalize().replace("_", " ") for period in time_periods]
        context['categories'] = Tag.objects.filter(major=True)
        context['selected_category'] = self.request.GET.get('category', '')
        context['searched_phrase'] = self.request.GET.get('search', '')


        return context
  
    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        image = Image.objects.get(pk=action)
        article = self.get_object()
        article.images.add(image)
        article.save()
        return redirect(reverse_lazy('newsharborapp:article-edit', kwargs={'pk': self.get_object().id}))


class TagListView(EditorOnlyMixin, generic.ListView):

    model = Tag
    template_name = 'newsharborapp/tag_list.html'
    context_object_name = 'tags'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['minor_tags'] = Tag.objects.filter(major=False)
        context['major_tags'] = Tag.objects.filter(major=True)
        return context
        

    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        if action == "create_tag":
            tags = request.POST.get('tag_name').split(",")
            [Tag.objects.create(name=tag.strip().capitalize()) for tag in tags]
        return redirect(request.path)


class TagDetailView(EditorOnlyMixin, generic.DetailView):
    
    model = Tag
    template_name = 'newsharborapp/tag_detail.html'
    context_object_name = 'tag'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        action = self.request.POST.get('action')
        tag = self.get_object()
        if action == "set_major":
            tag.major = True
            tag.save()
        if action == "set_minor":
            tag.major = False
            tag.save()
        if "unassign_article" in action:
            pk = action.rsplit("_")[-1]
            article = Article.objects.get(pk=pk)
            tag.articles.remove(article)
        if "unassign_image" in action:
            pk = action.rsplit("_")[-1]
            image = Image.objects.get(pk=pk)
            tag.images.remove(image)
        if action == "delete_tag":
            tag.delete()
            return redirect(reverse_lazy('newsharborapp:tags'))
        return redirect(request.path)
    

#################### API ######################################


class ApiArticleListView(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Article.objects.filter(for_display=True)
    serializer_class = ArticleSerializer
    permission_classes = [IsEditorOrReadOnlyPermission]

    def get_queryset(self):
        queryset = Article.objects.all()
        tags = (self.request.GET.get('tags'))
        if tags:
            search_words = clean_search_phrase(tags)
            tags = Tag.objects.filter(name__in=search_words)
            if tags.exists():
                queryset = queryset.filter(tags__in=tags)
            else:
                queryset = Article.objects.none()
        queryset = queryset.distinct()
        return queryset
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ApiArticleDetailView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [ArticleApiViewCustomPermission]


    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        article = self.get_object()
        user = request.user
        command = request.data.get('command')
        topic = request.data.get('generate')
        tags_to_add = request.data.get('add_tags')
        tags_to_remove = request.data.get('remove_tags')
        if command:
            if command == 'like':
                article.fans.add(user)
                return Response({'status': 'liked'}, status=status.HTTP_200_OK)
            elif command == 'dislike':
                article.fans.remove(user)
                return Response({'status': 'disliked'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid command'}, status=status.HTTP_400_BAD_REQUEST)
        elif topic:
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
            return self.retrieve(request, *args, **kwargs)
        elif tags_to_add:
            tags = tags_to_add.split(',')
            for tag_name in tags:
                tag_name = tag_name.strip().capitalize()
                tag = Tag.objects.filter(name=tag_name).first()
                if not tag:
                    tag = Tag.objects.create(name=tag_name)
                    tag.save()
                tag.articles.add(article)
            return self.retrieve(request, *args, **kwargs)
        elif tags_to_remove:
            tags = tags_to_remove.split(',')
            for tag in tags:
                tag = Tag.objects.filter(name=tag).first()
                if tag:
                    tag.articles.remove(article)
            return self.retrieve(request, *args, **kwargs)
        
        return self.update(request, *args, **kwargs)
        

class ApiParagraphListView(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Paragraph.objects.all()
    serializer_class = ParagraphSerializer

    def get_queryset(self):
        article = (self.request.GET.get('article'))
        if article:
            if article.isnumeric():
                article_obj = Article.objects.get(pk=article)      
                return Paragraph.objects.filter(article=article_obj)
        return Paragraph.objects.all()
        
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
class ApiParagraphDetailView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = Paragraph.objects.all()
    serializer_class = ParagraphSerializer
    permission_classes = [EditorOnlyPermission]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class ApiImageListView(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [EditorOnlyPermission]

    def get_queryset(self):
        queryset = Image.objects.all()
        tags = (self.request.GET.get('tags'))
        if tags:
            search_words = clean_search_phrase(tags)
            tags = Tag.objects.filter(name__in=search_words)
            if tags.exists():
                queryset = queryset.filter(tags__in=tags)
            else:
                queryset = Image.objects.none()
        queryset = queryset.distinct()
        return queryset
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ApiImageDetailView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [EditorOnlyPermission]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        image = self.get_object()
        tags_to_add = request.data.get('add_tags')
        tags_to_remove = request.data.get('remove_tags')
        if tags_to_add:
            tags = tags_to_add.split(',')
            for tag_name in tags:
                tag_name = tag_name.strip().capitalize()
                tag = Tag.objects.filter(name=tag_name).first()
                if not tag:
                    tag = Tag.objects.create(name=tag_name)
                    tag.save()
                tag.images.add(image)
            return self.retrieve(request, *args, **kwargs)
        elif tags_to_remove:
            tags = tags_to_remove.split(',')
            for tag in tags:
                tag = Tag.objects.filter(name=tag).first()
                if tag:
                    tag.images.remove(image)
            return self.retrieve(request, *args, **kwargs)
        return self.update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    

class ApiTagListView(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagListSerializer
    permission_classes = [EditorOnlyPermission]
    
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    

class ApiTagDetailView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagDetailSerializer
    permission_classes = [EditorOnlyPermission]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    

class ApiCommentListView(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = []

    def get_queryset(self):
        queryset = Comment.objects.all()
        article_id = (self.request.GET.get('article'))
        if article_id:
            article = Article.objects.get(pk=article_id)
            return article.comments
        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    

class ApiCommentDetailView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [CommentApiViewCustomPermission]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        comment = self.get_object()
        user = request.user
        command = request.data.get('command')
        if command:
            if command == 'like':
                comment.fans.add(user)
                comment.haters.remove(user)
                return Response({'status': 'liked'}, status=status.HTTP_200_OK)
            elif command == 'dislike':
                comment.fans.remove(user)
                comment.haters.add(user)
                return Response({'status': 'disliked'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid command'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return self.update(request, *args, **kwargs)