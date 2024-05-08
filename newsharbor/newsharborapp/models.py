import datetime
from django.db import models
from django.contrib.auth.models import User, Group
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils import timezone

from django.contrib import admin
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    name = models.CharField(max_length=255, default='profile')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_editor = models.BooleanField(default=False)

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
        if not self.name or self.name == "profile":
            self.name = self.get_profile_name()
        super().save(*args, **kwargs)


class Article(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=None, null=True)
    for_display = models.BooleanField(default=False)
    popularity = models.IntegerField(default=0)
    pub_date = models.DateTimeField(verbose_name="date published", auto_now=True)

    def __str__(self):
        return self.title


class Paragraph(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="paragraphs")
    text = models.TextField(default='', blank=True)
    is_lead = models.BooleanField(default=False)

    class Meta:
        unique_together = ('article', 'is_lead')


class Image(models.Model):

    name = models.CharField(max_length=255, default="image", blank=True)
    articles = models.ManyToManyField(Article, related_name="images", blank=True, null=True)
    photo = models.ImageField(upload_to='article_images/')
    pub_date = models.DateTimeField(verbose_name="date published", auto_now_add=True, blank=True)
    

    def __str__(self):
        return self.name
    
    def get_name(self):
        prefix = "image_"
        if self.articles.exists():
            name = prefix + self.articles.first().title.lower().replace(" ", "_")
        elif self.pub_date:
            name = prefix + str(self.pub_date)
        else:
            name = "image"
        return name
    
    def date(self):
        return self.pub_date.date()
        
    def save(self, *args, **kwargs):
        if not self.name or self.name == 'image':
            self.name = self.get_name()
        super().save(*args, **kwargs)


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="comments")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments', default=1)
    text = models.TextField(default='', blank=True)
    votes_up = models.IntegerField(default=0)
    votes_down = models.IntegerField(default=0)

    def __str__(self):
        return self.text
    
    def check_sentiment(self):
        return self.votes_up - self.votes_down