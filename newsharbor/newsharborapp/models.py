import datetime

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone



class Profile(models.Model):
    name = models.CharField(max_length=255, default='profile')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_editor = models.BooleanField(default=False)
    is_editor_in_chief = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    def get_profile_name(self):
        return "profile_" + self.user.username
    
    def belong_to(self, group_name):
        if self.user.groups.filter(name = group_name):
            return True
        else:
            return False

    def save(self, *args, **kwargs):
        if self.belong_to("Editor"):
            self.is_editor = True
        if self.belong_to("Editor in Chief"):
            self.is_editor_in_chief = True
        if not self.name or self.name == "profile":
            self.name = self.get_profile_name()
        super().save(*args, **kwargs)


class Article(models.Model):
    title = models.CharField(max_length=255, default="New article")
    author = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=None, null=True)
    for_display = models.BooleanField(default=False)
    unique_visitors = models.ManyToManyField(User, related_name="viewed_articles", blank=True)
    fans = models.ManyToManyField(User, related_name="liked_articles", blank=True)
    pub_date = models.DateTimeField(verbose_name="date published", auto_now_add=True)
    access = models.ManyToManyField(User, related_name="has_access", blank=True)
    access_required = models.BooleanField(default=False)
    time_periods = ['published_today', 'published_last_day', 'published_last_week', 'published_last_month']

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.id:
            if self.author and not self.access.filter(pk=self.author.pk).exists():
                self.access.add(self.author)
        super().save(*args, **kwargs)
    
    def get_date(self):
        return self.pub_date.strftime('%#m.%d.%Y %H:%M')
    
    def get_time_periods(self):
        return ['published_today', 'published_last_day', 'published_last_week', 'published_last_month']
    
    def published_today(self):
        return timezone.now().date() == self.pub_date.date()
    
    def published_last_day(self):
        return self.pub_date.date() >= timezone.now().date() - datetime.timedelta(days=1)
    
    def published_last_week(self):
        return self.pub_date.date() >= timezone.now().date() - datetime.timedelta(days=7)
    
    def published_last_month(self):
        return self.pub_date.date() >= timezone.now().date() - datetime.timedelta(days=30)


class Paragraph(models.Model):
    title = models.CharField(max_length=255, default="paragraph")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="paragraphs")
    text = models.TextField(default='', blank=True)
    is_lead = models.BooleanField(default=False)

    def save(self, *args, **kwargs) -> None:        
        if self.is_lead:
            existing_lead_paragraph = Paragraph.objects.filter(article=self.article, is_lead=True).first()
            if existing_lead_paragraph and existing_lead_paragraph != self:
                raise ValidationError('There can only be one lead paragraph per article.')
        
        super().save(*args, **kwargs)

    def clean(self):
        if self.is_lead and self.article.paragraphs.filter(is_lead=True).exists() and self.article.paragraphs.filter(is_lead=True).first() != self:
            raise ValidationError('There can only be one lead paragraph per article.')

    def __str__(self):
        return self.title

class Image(models.Model):

    name = models.CharField(max_length=255, default="image", blank=True)
    articles = models.ManyToManyField(Article, related_name="images", blank=True)
    photo = models.ImageField(upload_to='article_images/')
    pub_date = models.DateTimeField(verbose_name="date published", auto_now_add=True, blank=True)
    
    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.name
    
    def get_name(self):
        if self.pub_date:
            name = "image_" + str(self.pub_date)
        else:
            name = "image"
        return name
    
    def date(self):
        return self.pub_date.date()
        
    def save(self, *args, **kwargs):
        if not self.name or self.name == 'image':
            self.name = self.get_name()
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=255)
    articles = models.ManyToManyField(Article, related_name="tags", blank=True)
    images = models.ManyToManyField(Image, related_name="tags", blank=True)
    major = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().capitalize()
        if not self.id:
            existing_tag = Tag.objects.filter(name=self.name).first()
            if not existing_tag:
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
        

class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="comments")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', default=1)
    text = models.TextField(default='', blank=True)
    pub_date = models.DateTimeField(verbose_name="date published", auto_now_add=True, blank=True, null=True)
    fans = models.ManyToManyField(User, related_name="liked_comments", blank=True)
    haters = models.ManyToManyField(User, related_name="disliked_comments", blank=True)


    def __str__(self):
        return self.text
    
    def get_date(self):
        return self.pub_date.strftime('%#m.%d.%Y %H:%M')