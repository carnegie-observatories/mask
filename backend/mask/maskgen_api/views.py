# maskgen_api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Object, Mask, ObjectList
from .serializers import ObjectSerializer
from .obs_file_formatting import generate_obj_file, generate_obs_file
from mask.docker_helper import run_command

import pandas as pd
import json
import os

MASKGEN_DIRECTORY = "/Users/maylinchen/downloads/maskgen-2.14-Darwin-12.6_arm64"
MASKGEN_CONTAINER_NAME = "maskgen-maskgen-1"
OBS_DIRECTORY = "/Users/maylinchen/Downloads/mask/backend/mask/maskgen_api/obs_files"


class ObjectViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        # add name input + store in a list
        uploaded_file_bytes = request.data.get("file").read()
        data_str = uploaded_file_bytes.decode('utf-8')
        data = json.loads(data_str)
        obj_list = ObjectList.objects.create(name=request.data.get("list_name"))
        created_objects = []
        for row in data:
            obj, _ = Object.objects.get_or_create(
                name=row.pop('name'),
                user_id=request.data.get("user_id"),
                type=row.pop('type'),
                right_ascension=float(row.pop('ra')),
                declination=float(row.pop('dec')),
                priority=int(row.pop('priority')),
                aux=row
            )
            created_objects.append(obj.id)
            obj_list.objects_list.add(obj)
        return Response({"created": created_objects, "obj_list": obj_list.name}, status=status.HTTP_201_CREATED)
    
    # get lists of objects
    @action(detail=False, methods=["get"], url_path="viewlist")
    def view_list(self, request):
        ObjectList.objects.all()
        list_name = request.query_params.get('list_name')
        print(list_name)
        object_lists = ObjectList.objects.filter(name=list_name)

        if not object_lists.exists():
            return Response({"error": f"No ObjectList found with name '{list_name}'"}, status=404)

        results = []

        for obj_list in object_lists:
            serialized_objects = ObjectSerializer(obj_list.objects_list.all(), many=True)
            results.append({
                "list_name": obj_list.name,
                "objects": serialized_objects.data
            })

        return Response(results)
    
    # delete obj


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
        os.getcwd()
        os.environ["MGPATH"] = MASKGEN_DIRECTORY
        result, feedback = run_command(f"cp {OBS_DIRECTORY}/{data['filename']}.obs {MASKGEN_DIRECTORY}")
        print(feedback)
        if result:
            result, feedback = run_command(f"{MASKGEN_DIRECTORY}/maskgen {data['filename']}.obs")
        if result:
            return Response({"created": obs_path}, status=status.HTTP_201_CREATED)
        else:
            return  Response({"error": feedback}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        return Response({"message": f"Preview generated for {pk}"})

    @action(detail=True, methods=["post"], url_path="validate")
    def validate_setup(self, request, pk=None):
        return Response({"message": f"Validated instrument: {pk}"})
