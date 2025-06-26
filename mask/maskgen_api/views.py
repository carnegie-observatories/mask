# maskgen_api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Object, Mask
from .obs_file_formatting import generate_obj_file, generate_obs_file
from mask.docker_helper import docker_copy_file_to, docker_run_command, docker_get_file

import pandas as pd
import json

MASKGEN_CONTAINER_NAME = "maskgen-maskgen-1"


class ObjectViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        uploaded_file_bytes = request.data.get("file").read()
        data_str = uploaded_file_bytes.decode('utf-8')
        data = json.loads(data_str)

        created_objects = []
        for row in data:
            obj, _ = Object.objects.get_or_create(
                name=row.pop('name'),
                type=row.pop('type'),
                right_ascension=float(row.pop('ra')),
                declination=float(row.pop('dec')),
                priority=int(row.pop('priority')),
                aux=row
            )
            created_objects.append(obj.id)
        return Response({"created": created_objects}, status=status.HTTP_201_CREATED)


class MaskViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        mask = Mask.objects.get(pk=pk)
        return Response({
            "name": pk,
            "status": mask.status,
            "features": mask.features,
            "instrument_config": mask.instrument_config,
            "instrument_setup": mask.instrument_setup,
            "objects_list": [
                {
                    "name": obj.name,
                    "type": obj.type,
                    "right_ascension": obj.right_ascension,
                    "declination": obj.declination,
                    "priority": obj.priority,
                } | obj.aux for obj in mask.objects_list.all()
            ]
        })

    @action(detail=False, methods=["post"], url_path="generate")
    def generate_mask(self, request):
        data = request.data
        obj_path = generate_obj_file(data['filename'], data['objects'])
        obs_path = generate_obs_file(data, [obj_path])

        docker_copy_file_to(MASKGEN_CONTAINER_NAME, obj_path, f"app/linux")
        docker_copy_file_to(MASKGEN_CONTAINER_NAME, obs_path, f"app/linux")

        docker_run_command(MASKGEN_CONTAINER_NAME, f"maskgen {data['filename']}")
        docker_get_file(MASKGEN_CONTAINER_NAME, f"/masks/{data['filename']}.SMF", "maskgen_api/smf_files")

        return Response({"created": obs_path}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        docker_run_command(MASKGEN_CONTAINER_NAME, f"maskgen {pk}")
        return Response({"message": f"Preview generated for {pk}"})

    @action(detail=True, methods=["post"], url_path="validate")
    def validate_setup(self, request, pk=None):
        return Response({"message": f"Validated instrument: {pk}"})
