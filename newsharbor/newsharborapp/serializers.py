from django.contrib.auth.models import User
from rest_framework import serializers
from newsharborapp.models import Article, Paragraph, Image, Tag, Comment, Profile
from django.urls import reverse


class ArticleSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='newsharborapp:article')
    author = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()


    class Meta:
        model = Article
        fields = ['url', 'title', 'author', 'text', 'pub_date', 'views', 'likes', 'comments']

    def get_author(self, obj):
        return obj.author.username
    
    def get_text(self, obj):
        paragraphs = obj.paragraphs.all()
        return {paragraph.title : paragraph.text for paragraph in paragraphs}
    
    def get_views(self, obj):
        viewers = obj.unique_visitors.all()
        return len(viewers)

    def get_likes(self, obj):
        fans = obj.fans.all()
        return len(fans)
    
    def get_comments(self, obj):
        comments = obj.comments.all()
        comment_list = []
        for comment in comments:
            likes = len(comment.fans.all())
            dislikes = len(comment.haters.all())
            dictionary = {
                'author': comment.author.username,
                'text': comment.text,
                'date': comment.pub_date,
                'likes': likes,
                'dislikes': dislikes
                }
            comment_list.append(dictionary)
        return comment_list

