# maskgen_api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from maskgen_api.models import Object, Mask, ObjectList, InstrumentConfig
from maskgen_api.serializers import ObjectSerializer

# from .models import ... If you want to create your own db models (not reccomended)

from .validator import validate

import json
import os

MASKGEN_DIRECTORY = "/Users/maylinchen/downloads/maskgen-2.14-Darwin-12.6_arm64/"
MASKGEN_CONTAINER_NAME = "maskgen-maskgen-1"
PROJECT_DIRECTORY = os.getcwd() + "/"
API_FOLDER = "maskgen_api/"


class ObjectViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        # info from request
        uploaded_file = request.data.get("file")
        uploaded_file_bytes = uploaded_file.read()
        user_id = request.data.get("user_id")
        list_name = request.data.get("list_name")

        # do file conversion if necessary (ie csv to JSON etc)
        # you want a variable named data that contains a dict
        data = uploaded_file_bytes  # temp, replace with actual code

        # Check if a list with the same name and user_id already exists
        existing = ObjectList.objects.filter(name=list_name, user_id=user_id).first()
        if existing:
            return Response(
                {"error": f"List '{list_name}' already exists for user '{user_id}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # creates object list
        obj_list = ObjectList.objects.create(name=list_name, user_id=user_id)
        created_objects = []

        """
        Populates object list with data
        This code assumes that each object will contain a type, ra, dec, and priority.
        Any extra info will end up in aux as a dict.

        Feel free to modify what parameters are stored, but you'll need to modify
        the object model in models.py in the SAME folder. Then, change the import at the top to
        use the local import.
        """
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

        # returns created object ids and the object list name
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
            # this only works if you are using the provided object model
            serialized_objects = ObjectSerializer(
                obj_list.objects_list.all(), many=True
            )
            results.append(
                {"list_name": obj_list.name, "objects": serialized_objects.data}
            )

        return Response(results)

    # TODO: delete obj


class MaskViewSet(viewsets.ViewSet):
    # does not need modification, can add more specific parameters to be included if desired
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
        """
        do whatever you need to run your mask cutting software
        make sure you clean up unnecessary files
        see maskgen_api for an example
        """

        # Validation of masks is also part of this process
        validate()  # defined in validator.py

        """
        Once you've created a mask, store it in the database for future reference
        You should also process and store feature info (slits, holes etc) in the Mask Object

        mask = Mask.objects.create(
            name=filename,
            status=Status.DRAFT,
            instrument_setup=data,
            instrument_version=InstrumentConfig.objects.filter(instrument=data["instrument"]).order_by("-version").first().version,
            features=features
        )
        """

        # remember to return some kind of HTTP response
        return Response("created", status=status.HTTP_201_CREATED)


# No need to change this
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
