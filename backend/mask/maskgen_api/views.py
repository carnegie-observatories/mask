# maskgen_api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Object, Mask, ObjectList
from .serializers import ObjectSerializer
from .obs_file_formatting import generate_obj_file, generate_obs_file, obj_to_json
from mask.docker_helper import run_command, run_maskgen

import pandas as pd
import json
import os

MASKGEN_DIRECTORY = "/Users/maylinchen/downloads/maskgen-2.14-Darwin-12.6_arm64/"
MASKGEN_CONTAINER_NAME = "maskgen-maskgen-1"
PROJECT_DIRECTORY = "/Users/maylinchen/Downloads/mask/backend/mask/"
API_FOLDER = "maskgen_api/"

class ObjectViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        uploaded_file = request.data.get("file")
        uploaded_file_bytes = uploaded_file.read()

        if uploaded_file.name.endswith(".obj"):
            data = obj_to_json(uploaded_file_bytes)
        else:
            data_str = uploaded_file_bytes.decode('utf-8')
            data = json.loads(data_str)
        user_id = request.data.get("user_id")
        list_name = request.data.get("list_name")

        # Check if a list with the same name and user_id already exists
        existing = ObjectList.objects.filter(name=list_name, user_id=user_id).first()
        if existing:
            return Response(
                {"error": f"List '{list_name}' already exists for user '{user_id}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        obj_list = ObjectList.objects.create(name=list_name, user_id=user_id)
        created_objects = []

        for row in data:
            obj, _ = Object.objects.get_or_create(
                name=row.pop('name'),
                user_id=request.data.get("user_id"),
                defaults={
                    "type": row.pop("type"),
                    "right_ascension": float(row.pop("ra")),
                    "declination": float(row.pop("dec")),
                    "priority": int(row.pop("priority")),
                    "aux": row,
                }
            )
            created_objects.append(obj.id)
            obj_list.objects_list.add(obj)
        return Response({"created": created_objects, "obj_list": obj_list.name}, status=status.HTTP_201_CREATED)
    
    # get lists of objects
    @action(detail=False, methods=["get"], url_path="viewlist")
    def view_list(self, request):
        ObjectList.objects.all()
        list_name = request.query_params.get('list_name')
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
        filename = data['filename']
        obj_path = generate_obj_file(filename, data['objects'])
        obs_path = generate_obs_file(data, [f"{filename}.obj"])
        os.environ["MGPATH"] = MASKGEN_DIRECTORY
        
        print("cping files")
        result, cp_feedback = run_command(f"cp {PROJECT_DIRECTORY}{API_FOLDER}obs_files/{filename}.obs {MASKGEN_DIRECTORY}")
        result, cp_feedback = run_command(f"cp {PROJECT_DIRECTORY}{API_FOLDER}obj_files/{filename}.obj {MASKGEN_DIRECTORY}")
        if result:
            print("running maskgen")
            result, feedback = run_maskgen(f"{MASKGEN_DIRECTORY}/maskgen -s {filename}.obs")
            print(feedback)
        if result and "Writing object file with use counts to" in feedback:
            print("moving smf files")
            run_command(f"mv {PROJECT_DIRECTORY}{filename}.SMF {PROJECT_DIRECTORY}{API_FOLDER}smf_files")
            return Response({"created": f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files/{filename}.SMF"}, status=status.HTTP_201_CREATED)
        else:
            return  Response({"error": feedback}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        mask_name = request.query_params.get('mask_name')
        run_command(f"{MASKGEN_DIRECTORY}/smdfplt {mask_name}")
        return Response({"message": f"Preview generated for {pk}"})

    @action(detail=True, methods=["post"], url_path="validate")
    def validate_setup(self, request, pk=None):
        return Response({"message": f"Validated instrument: {pk}"})
