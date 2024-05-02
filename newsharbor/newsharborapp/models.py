import datetime
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.utils import timezone

from django.contrib import admin
from django.db import models
from django.utils import timezone


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

    name = models.CharField(max_length=255, default="image")
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="images")
    photo = models.ImageField(upload_to='article_images/')
    is_lead = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('article', 'is_lead')

    def __str__(self):
        return self.name
    
    def get_name(self):
        prefix = "image_"
        if self.is_lead:
            prefix = "lead_image_"
        return prefix + self.article.title.lower().replace(" ", "_")
        
    def save(self, *args, **kwargs):
        if not self.name or self.name == "image":
            self.name = self.get_name()
        super().save(*args, **kwargs)