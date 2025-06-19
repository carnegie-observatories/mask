from django.urls import path
from .views import UploadObjectsView, MaskView, MakeFeatureView, FeatureView


urlpatterns = [
    path('createmask/objects/', UploadObjectsView.as_view(), name='upload_objs'),
    path('mask/<str:name>/', MaskView.as_view(), name='mask'),
    path('mask/<str:name>/features/', MakeFeatureView.as_view(), name='make_feature'),
    path('mask/<str:name>/features/<int:feature_id>/', FeatureView.as_view(), name='feature_id'),
]