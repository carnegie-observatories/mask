# maskgen_api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaskViewSet, ObjectViewSet

router = DefaultRouter()
router.register(r'masks', MaskViewSet, basename='mask')
router.register(r'objects', ObjectViewSet, basename='object')

urlpatterns = [
    path("", include(router.urls)),
]
