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
        fields = ['url', 'id', 'title', 'author', 'text', 'pub_date', 'views', 'likes', 'comments']

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
    
    
    def create(self, validated_data):
        user = self.context['request'].user
        article = Article.objects.create(author=user, **validated_data)
        return article
    

class ParagraphSerializer(serializers.ModelSerializer):

    class Meta:
        model = Paragraph
        fields = ['id', 'article', 'title', 'text', 'is_lead']

    def create(self, validated_data):
        request = self.context.get('request', None)
        if request:
            article_id = request.data.get('article', None)
            if article_id:
                paragraphs_exist = Paragraph.objects.filter(article=article_id)
                is_lead = False if paragraphs_exist else True
                title = request.data.get('title', 'New Paragraph')
                text = request.data.get('text', 'Paragraph text')
                article = Article.objects.get(pk=article_id)
                return Paragraph.objects.create(article=article, title=title, text=text, is_lead=is_lead)
            else:
                raise serializers.ValidationError("Incorect data provided")
        else:
            raise serializers.ValidationError("Request context is not available")

    def update(self, instance, validated_data):
        validated_data.pop('is_lead', None)
        return super().update(instance, validated_data)

class ImageSerializer(serializers.ModelSerializer):
    articles = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'name', 'photo', 'articles', 'pub_date', 'tags']

    def get_articles(self, obj):
        return [article.title for article in obj.articles.all()]
    
    def get_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]
    

class TagListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name', 'major']


class TagDetailSerializer(serializers.ModelSerializer):
    articles = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'major', 'articles', 'images']

    def get_articles(self, obj):
        return [article.id for article in obj.articles.all()]
    
    def get_images(self, obj):
        return [image.id for image in obj.images.all()]
    
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    article = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'article', 'text', 'pub_date', 'likes', 'dislikes']

    def get_author(self, obj):
        return obj.author.username

    def get_article(self, obj):
        return {"id": obj.article.id, "title": obj.article.title}
    
    def get_likes(self, obj):
        return len(obj.fans.all())
    
    def get_dislikes(self, obj):
        return len(obj.haters.all())
    
    def create(self, validated_data):
        user = self.context['request'].user
        request = self.context.get('request', None)
        if request:
            article_id = request.data.get('article', None)
            if article_id:
                text = request.data.get('text', 'Paragraph text')
                article = Article.objects.get(pk=article_id)
                return Comment.objects.create(author=user, article=article, text=text)
            else:
                raise serializers.ValidationError("Incorect data provided")
        else:
            raise serializers.ValidationError("Request context is not available")