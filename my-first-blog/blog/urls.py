from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register('Post', views.blogImage)

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('api_root/', include(router.urls)),
]
