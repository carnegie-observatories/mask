
from rest_framework import serializers
from .models import Object

class UploadObjectSerializer(serializers.ModelSerializer):
    file_uploaded = serializers.FileField()
    class Meta:
        fields = ['file_uploaded']

class ObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Object
        fields = '__all__'


