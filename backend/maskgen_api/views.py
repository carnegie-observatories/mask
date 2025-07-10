# maskgen_api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Object, Mask, ObjectList, InstrumentConfig, Status
from .serializers import ObjectSerializer
from .obs_file_formatting import (
    generate_obj_file,
    generate_obs_file,
    obj_to_json,
    categorize_objs,
)
from backend.terminal_helper import run_command, run_maskgen

import json
import os

MASKGEN_DIRECTORY = "/Users/maylinchen/downloads/maskgen-2.14-Darwin-12.6_arm64/"
MASKGEN_CONTAINER_NAME = "maskgen-maskgen-1"
PROJECT_DIRECTORY = os.getcwd() + "/"
API_FOLDER = "maskgen_api/"


class ObjectViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        uploaded_file = request.data.get("file")
        uploaded_file_bytes = uploaded_file.read()

        # check if file is .obj or json
        if uploaded_file.name.endswith(".obj"):
            data = obj_to_json(uploaded_file_bytes)
        else:
            data_str = uploaded_file_bytes.decode("utf-8")
            data = json.loads(data_str)

        user_id = request.data.get("user_id")
        list_name = request.data.get("list_name")

        # Check if a list with the same name and user_id already exists
        existing = ObjectList.objects.filter(name=list_name, user_id=user_id).first()
        if existing:
            return Response(
                {"error": f"List '{list_name}' already exists for user '{user_id}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj_list = ObjectList.objects.create(name=list_name, user_id=user_id)
        created_objects = []

        for row in data:
            obj, _ = Object.objects.get_or_create(
                name=row.pop("name"),
                user_id=request.data.get("user_id"),
                defaults={
                    "type": row.pop("type"),
                    "right_ascension": float(row.pop("ra")),
                    "declination": float(row.pop("dec")),
                    "priority": int(row.pop("priority")),
                    "aux": row,
                },
            )
            created_objects.append(obj.id)
            obj_list.objects_list.add(obj)
        return Response(
            {"created": created_objects, "obj_list": obj_list.name},
            status=status.HTTP_201_CREATED,
        )

    # get lists of objects
    @action(detail=False, methods=["get"], url_path="viewlist")
    def view_list(self, request):
        list_name = request.query_params.get("list_name")
        object_lists = ObjectList.objects.filter(name=list_name)

        if not object_lists.exists():
            return Response(
                {"error": f"No ObjectList found with name '{list_name}'"}, status=404
            )

        results = []

        for obj_list in object_lists:
            serialized_objects = ObjectSerializer(
                obj_list.objects_list.all(), many=True
            )
            results.append(
                {"list_name": obj_list.name, "objects": serialized_objects.data}
            )

        return Response(results)

    # TODO: delete obj


class MaskViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        mask = Mask.objects.get(name=pk)
        return Response(
            {
                "name": pk,
                "status": mask.status,
                "instrument_version": mask.instrument_version,
                "instrument_setup": mask.instrument_setup,
                "objects_list": [
                    {
                        "name": obj.name,
                        "type": obj.type,
                        "right_ascension": obj.right_ascension,
                        "declination": obj.declination,
                        "priority": obj.priority,
                    }
                    | (obj.aux or {})
                    for obj in mask.objects_list.all()
                ],
                "excluded_objects": [
                    {
                        "name": obj.name,
                        "type": obj.type,
                        "right_ascension": obj.right_ascension,
                        "declination": obj.declination,
                        "priority": obj.priority,
                    }
                    | (obj.aux or {})
                    for obj in mask.excluded_obj_list.all()
                ],
                "features": mask.features,
            }
        )

    @action(detail=False, methods=["post"], url_path="generate")
    def generate_mask(self, request):
        data = request.data
        filename = data["filename"]
        generate_obj_file(filename, data["objects"])
        generate_obs_file(data, [f"{filename}.obj"])
        os.environ["MGPATH"] = MASKGEN_DIRECTORY

        result, _ = run_command(
            f"cp {PROJECT_DIRECTORY}{API_FOLDER}obs_files/{filename}.obs {MASKGEN_DIRECTORY}"
        )
        result, _ = run_command(
            f"cp {PROJECT_DIRECTORY}{API_FOLDER}obj_files/{filename}.obj {MASKGEN_DIRECTORY}"
        )
        if result:
            result, feedback = run_maskgen(
                f"{MASKGEN_DIRECTORY}/maskgen -s {filename}.obs"
            )

        if result and "Writing object file with use counts to" in feedback:
            # clean up auto generated files
            run_command(
                f"mv {PROJECT_DIRECTORY}{filename}.SMF {PROJECT_DIRECTORY}{API_FOLDER}smf_files"
            )
            run_command(f"rm -f {PROJECT_DIRECTORY}.loc_mgvers.dat")
            run_command(f"rm -f {PROJECT_DIRECTORY}.loc_ociw214.pem")

            # process features from SMF
            filepath = os.path.join(
                PROJECT_DIRECTORY, API_FOLDER, "smf_files", f"{filename}.SMF"
            )
            features = []
            with open(filepath, "rb") as f:

                for line in f:
                    line = line.decode("utf-8").strip()
                    if line.startswith("SLIT"):
                        parts = line.split()
                        features.append(
                            {
                                "type": "SLIT",
                                "id": parts[1],
                                "ra": parts[2],
                                "dec": parts[3],
                                "x": float(parts[4]),
                                "y": float(parts[5]),
                                "width": float(parts[6]),
                                "a_len": float(parts[7]),
                                "b_len": float(parts[8]),
                                "angle": float(parts[9]),
                            }
                        )
                    elif line.startswith("HOLE"):
                        parts = line.split()
                        features.append(
                            {
                                "type": "HOLE",
                                "id": parts[1],
                                "ra": parts[2],
                                "dec": parts[3],
                                "x": float(parts[4]),
                                "y": float(parts[5]),
                                "width": float(parts[6]),
                                "shape_code": int(parts[7]),
                                "a_len": float(parts[8]),
                                "b_len": float(parts[9]),
                                "angle": float(parts[10]),
                            }
                        )

            mask = Mask.objects.create(
                name=filename,
                status=Status.DRAFT,
                instrument_setup=data,
                instrument_version=InstrumentConfig.objects.filter(
                    instrument=data["instrument"]
                )
                .order_by("-version")
                .first()
                .version,
                features=features,
            )

            result, feedback = categorize_objs(
                mask, f"{PROJECT_DIRECTORY}{filename}.obw"
            )
            run_command(f"rm -f {PROJECT_DIRECTORY}{filename}.obw")
            if result:
                return Response(
                    {
                        "created": f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files/{filename}.SMF"
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response({"error": "error"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "error"}, status=status.HTTP_400_BAD_REQUEST)


class InstrumentViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        version = request.query_params.get("version")
        if version:
            config = get_object_or_404(InstrumentConfig, instrument=pk, version=version)
        else:
            config = (
                InstrumentConfig.objects.filter(instrument=pk)
                .order_by("-version")
                .first()
            )

        return Response(
            {
                "name": config.instrument,
                "filters": config.filters,
                "dispersers": config.dispersers,
                "aux": config.aux,
            }
        )

    @action(detail=False, methods=["post"], url_path="uploadconfig")
    def upload(self, request):
        print(request.data)
        data = request.data
        existing = (
            InstrumentConfig.objects.filter(instrument=data["instrument"])
            .order_by("-version")
            .first()
        )
        if existing:
            version = existing.version + 1
        else:
            version = 1

        instrument_config = InstrumentConfig.objects.create(
            instrument=data.pop("instrument"),
            filters=data.pop("filters"),
            dispersers=data.pop("dispersers"),
            aux=json.dumps(data),
            version=version,
        )

        return Response(
            {"created": str(instrument_config)}, status=status.HTTP_201_CREATED
        )
