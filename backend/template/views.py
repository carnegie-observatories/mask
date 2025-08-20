# maskgen_api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from maskgen_api.models import (
    Object,
    Mask,
    ObjectList,
    InstrumentConfig,
    Image,
    Project,
)
from backend.terminal_helper import remove_file

# from .models import ... If you want to create your own db models (not reccomended)

from .validator import validate

import json


# It's reccommended you follow this structure for projects
# Note that masks and images are directly related to project
class ProjectViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="create")
    def upload(self, request):
        print(request.headers)
        user_id = request.headers.get("user-id")
        proj_name = request.data.get("project_name")
        existing = ObjectList.objects.filter(name=proj_name, user_id=user_id).first()
        if existing:
            return Response(
                {
                    "error": f"Project '{proj_name}' already exists for user '{user_id}'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        project = Project.objects.create(
            name=proj_name,
            user_id=user_id,
            center_ra=request.data.get("center_ra"),
            center_dec=request.data.get("center_dec"),
        )
        if project:
            return Response(
                {"created": {"name": project.name, "user_id": project.user_id}},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response({"error"}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        user_id = request.headers.get("user-id")
        project = get_object_or_404(Project, name=pk, user_id=user_id)
        image_names = list(project.images.values_list("name", flat=True))
        mask_names = list(project.masks.values_list("name", flat=True))
        return Response(
            {
                "project": project.name,
                "user_id": project.user_id,
                "images": image_names,
                "masks": mask_names,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["delete"], url_path="delete")
    def delete_project(self, request):
        user_id = request.headers.get("user-id")
        proj_name = request.data.get("project_name")
        existing = Project.objects.filter(name=proj_name, user_id=user_id).first()
        existing.delete()
        return Response(
            {"message": "project deleted"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="list")
    def list_projects(self, request):
        user_id = request.headers.get("user-id")
        if not user_id:
            return Response(
                {"error": "missing user-id header"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        projects = Project.objects.filter(user_id=user_id).values("name")

        return Response(
            {"projects": list(projects)},
            status=status.HTTP_200_OK,
        )


# don't need to change if not modifying project setup
class ImageViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["get"], url_path="getimg")
    def get_image(self, request):
        user_id = request.headers.get("user-id")
        img_name = request.query_params.get("img_name")
        proj_name = request.query_params.get("project_name")
        print(proj_name)
        project = Project.objects.get(name=proj_name, user_id=user_id)
        print(project.images)
        if project:
            img_obj = project.images.get(name=img_name)
            img_path = img_obj.image.path
            return FileResponse(open(img_path, "rb"), content_type="image/jpeg")

    @action(detail=False, methods=["post"], url_path="uploadimg")
    def upload(self, request):
        proj_name = request.data["project_name"]
        uploaded_img = request.FILES.get("image")
        image = Image.objects.create(image=uploaded_img, name=uploaded_img.name)
        project = Project.objects.get(name=proj_name)
        project.images.add(image)
        project.save()
        return Response(
            {"message": "Image uploaded successfully", "image_url": image.image.url},
            status=status.HTTP_200_OK,
        )


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
            results.append({"list_name": obj_list.name})

        return Response(results)

    @action(detail=False, methods=["get"], url_path="list_all")
    def list_obj_lists(self, request):
        user_id = request.headers.get("user-id")
        if not user_id:
            return Response(
                {"error": "missing user-id header"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj_lists = ObjectList.objects.filter(user_id=user_id).values("name")

        return Response(
            {"object lists": list(obj_lists)},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["delete"], url_path="delete")
    def delete_obj(self, request):
        list_name = request.query_params.get("list_name")
        obj_name = request.query_params.get("obj_name")
        user_id = request.headers.get("user-id")
        obj_list = get_object_or_404(ObjectList, name=list_name, user_id=user_id)
        obj = get_object_or_404(obj_list.objects, name=obj_name)
        obj_list.objects_list.remove(obj)
        obj.delete()
        return Response(
            {"message": f"object '{obj_name}' deleted"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["patch"], url_path="edit")
    def edit_obj(self, request):
        list_name = request.data.pop("list_name")
        obj_name = request.data.pop("obj_name")
        user_id = request.headers.get("user-id")

        obj_list = get_object_or_404(ObjectList, name=list_name, user_id=user_id)
        obj = obj_list.objects_list.get(name=obj_name)

        if "type" in request.data:
            obj.type = request.data.pop("type")
        if "ra" in request.data:
            obj.right_ascension = float(request.data.pop("ra"))
        if "dec" in request.data:
            obj.declination = float(request.data.pop("dec"))
        if "priority" in request.data:
            obj.priority = int(request.data.pop("priority"))
        if request.data:
            obj.aux.update(request.data)

        obj.save()

        return Response(
            {"message": f"Object '{obj_name}' updated"}, status=status.HTTP_200_OK
        )


class MaskViewSet(viewsets.ViewSet):
    # does not need modification, can add more specific parameters to be included if desired
    def retrieve(self, request, pk=None):
        proj_name = request.query_params.get("project_name")
        user_id = request.headers.get("user-id")
        project = Project.objects.get(name=proj_name, user_id=user_id)
        mask = project.masks.get(name=pk)

        return Response(
            {
                "name": pk,
                "status": mask.status,
                "instrument_version": mask.instrument_version,
                "instrument_setup": mask.instrument_setup,
                "objects_list": mask.objects_list.name,
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
        Remember the way you should be finding masks is to first find the project their in, then find them in project.masks
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

    @action(detail=False, methods=["delete"], url_path="delete")
    def delete_mask(self, request):
        user_id = request.headers.get("user-id")
        mask_name = request.query_params.get("mask_name")
        proj_name = request.query_params.get("project_name")

        if not (user_id and mask_name and proj_name):
            return Response(
                {"error": "missing required parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project = get_object_or_404(Project, name=proj_name, user_id=user_id)

        try:
            mask = project.masks.get(name=mask_name)
        except Mask.DoesNotExist:
            return Response(
                {"error": "mask not found in this project"},
                status=status.HTTP_404_NOT_FOUND,
            )

        file_paths = []  # put files generated as part of mask gen process here
        for file_path in file_paths:
            remove_file(file_path)

        project.masks.remove(mask)
        mask.delete()

        return Response(
            {"message": f"mask '{mask_name}' deleted successfully"},
            status=status.HTTP_200_OK,
        )


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


class MachineViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="generate")
    def generate_machine_code(self, request):
        # write your machine code generation here, store it appropriately as a file in a folder
        # so that you can access it later
        return Response("created", status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="get-machine-code")
    def get_machine_code(self, request):
        # fill in your access code here, remember to change content_type in file response to match
        file_path = "filler"
        return FileResponse(open(file_path, "rb"), content_type="application/x-netcdf")
