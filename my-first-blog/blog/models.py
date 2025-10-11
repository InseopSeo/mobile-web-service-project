from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.

class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date= models.DateTimeField(default=timezone.now)
    published_date= models.DateTimeField(blank=True, null=True)
    image = models.ImageField(upload_to='blog_image/%Y/%m/%d/', default='blog_image/default_error.png')

    def publish(self):
        self.published_date= timezone.now()
        self.save()

    def __str__(self):
        return self.title