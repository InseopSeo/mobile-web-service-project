from blog.models import Post
from rest_framework import serializers
from django.contrib.auth.models import User

class PostSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Post
        fields = ['author', 'title', 'text', 'created_date', 'published_date', 'image']