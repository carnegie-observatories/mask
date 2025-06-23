from django.urls import path
from .views import UploadObjectsView, MaskView, MakeFeatureView, FeatureView, UploadInstrumSetup


urlpatterns = [
    path('createmask/upload_objects/', UploadObjectsView.as_view(), name='upload_objs'),
    path('createmask/upload_instrum_setup/', UploadInstrumSetup.as_view(), name='upload_instrum_setup'),
    path('mask/<str:name>/', MaskView.as_view(), name='mask'),
    path('mask/<str:name>/features/', MakeFeatureView.as_view(), name='make_feature'),
    path('mask/<str:name>/features/<int:feature_id>/', FeatureView.as_view(), name='feature_id'),
]