from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils import timezone


class Article(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default='unknown')
    for_display = models.BooleanField(default=False)
    popularity = models.IntegerField(default=0)


class Paragraph(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    text = models.TextField(default='', blank=True)
    is_lead = models.BooleanField(default=False)


class Image(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='article_images/')