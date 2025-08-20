from rest_framework import serializers
from .models import Object, Mask


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


class MaskSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()

    class Meta:
        model = Mask
        fields = ["id", "name", "status", "project_name", "user_id"]

    def get_project_name(self, obj):
        project = obj.project_set.first()
        return project.name if project else None
