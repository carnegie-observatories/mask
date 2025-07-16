# maskgen_api/urls.py
from rest_framework.routers import DefaultRouter
from .views import (
    MaskViewSet,
    ObjectViewSet,
    InstrumentViewSet,
    ImageViewSet,
    ProjectViewSet,
)

router = DefaultRouter()
router.register(r"masks", MaskViewSet, basename="mask")
router.register(r"objects", ObjectViewSet, basename="object")
router.register(r"instruments", InstrumentViewSet, basename="instrum")
router.register(r"images", ImageViewSet, basename="image")
router.register(r"project", ProjectViewSet, basename="project")

urlpatterns = router.urls
