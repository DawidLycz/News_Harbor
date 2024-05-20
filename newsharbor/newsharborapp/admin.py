from django.contrib import admin
from .models import *


admin.site.register(Profile)
admin.site.register(Article)
admin.site.register(Paragraph)
admin.site.register(Image)
admin.site.register(Tag)
admin.site.register(Comment)