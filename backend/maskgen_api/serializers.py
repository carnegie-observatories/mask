from rest_framework import serializers
from .models import Object


class UploadObjectSerializer(serializers.ModelSerializer):
    file_uploaded = serializers.FileField()

    class Meta:
        fields = ["file_uploaded"]


class ObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Object
        fields = [
            "id",
            "name",
            "type",
            "user_id",
            "right_ascension",
            "declination",
            "priority",
            "aux",
        ]
