# maskgen_api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import FileResponse

from astropy.table import Table

from .models import Object, Mask, ObjectList, InstrumentConfig, Status, Project, Image
from .serializers import ObjectSerializer, MaskSerializer
from .obs_file_formatting import (
    generate_obj_file,
    generate_obs_file,
    obj_to_json,
    categorize_objs,
    to_deg,
)
from backend.terminal_helper import run_maskgen, run_maskcut, remove_file
from .validator import validate
import json
import os
import io
import shutil

MASKGEN_DIRECTORY = "/Users/maylinchen/downloads/maskgen-2.14-Darwin-12.6_arm64/"
PROJECT_DIRECTORY = os.getcwd() + "/"
API_FOLDER = "maskgen_api/"


class ProjectViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="create")
    def upload(self, request):
        user_id = request.headers.get("user-id")
        proj_name = request.data.get("project_name")
        existing = Project.objects.filter(name=proj_name, user_id=user_id).first()
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
            return Response(
                {"error": "project not created"}, status=status.HTTP_400_BAD_REQUEST
            )

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
        if not existing:
            return Response(
                {
                    "error": f"Project '{proj_name}' does not exist for user '{user_id}'."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
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


class InstrumentViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        version = request.query_params.get("version")
        if version:
            config = get_object_or_404(InstrumentConfig, instrument=pk, version=version)
        else:
            config = get_object_or_404(
                InstrumentConfig.objects.order_by("-version"), instrument=pk
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


class ImageViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["get"], url_path="getimg")
    def get_image(self, request):
        user_id = request.headers.get("user-id")
        img_name = request.query_params.get("img_name")
        proj_name = request.query_params.get("project_name")
        project = get_object_or_404(Project, name=proj_name, user_id=user_id)
        img_obj = project.images.get(name=img_name)
        img_path = img_obj.image.path
        return FileResponse(open(img_path, "rb"), content_type="image/jpeg")

    @action(detail=False, methods=["post"], url_path="uploadimg")
    def upload(self, request):
        proj_name = request.data["project_name"]
        user_id = request.headers.get("user-id")
        uploaded_img = request.FILES.get("image")
        image = Image.objects.create(image=uploaded_img, name=uploaded_img.name)
        project = get_object_or_404(Project, name=proj_name, user_id=user_id)
        project.images.add(image)
        project.save()
        return Response(
            {"message": "Image uploaded successfully", "image_url": image.image.url},
            status=status.HTTP_200_OK,
        )


class ObjectViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        user_id = request.headers.get("user-id")
        list_name = request.data.get("list_name")
        proj_name = request.data.get("project_name")
        project = Project.objects.get(name=proj_name, user_id=user_id)

        uploaded_file = request.data.get("file")
        uploaded_file_bytes = uploaded_file.read()

        # check if file is .obj or json
        if uploaded_file.name.endswith(".obj"):
            data = obj_to_json(uploaded_file_bytes)
        elif uploaded_file.name.endswith(".csv"):
            table = Table.read(io.BytesIO(uploaded_file_bytes), format="csv")
            data = table.to_pandas().to_dict(orient="records")
        else:
            data_str = uploaded_file_bytes.decode("utf-8")
            data = json.loads(data_str)

        # Check if a list with the same name and user_id already exists
        existing = ObjectList.objects.filter(name=list_name, user_id=user_id).first()
        if existing:
            return Response(
                {"error": f"List '{list_name}' already exists for user '{user_id}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj_list = ObjectList.objects.create(
            name=list_name, user_id=user_id, project_name=proj_name
        )

        for row in data:
            # convert hours to degs if in hrs
            ra, dec = to_deg(row.pop("ra"), row.pop("dec"))

            obj = Object.objects.create(
                name=row.pop("name"),
                user_id=request.headers.get("user-id"),
                type=row.pop("type"),
                right_ascension=ra,
                declination=dec,
                priority=int(row.pop("priority")),
                aux=row,
            )
            obj_list.objects_list.add(obj)

        project.obj_list = obj_list
        project.save()
        return Response(
            {"obj_list": obj_list.name},
            status=status.HTTP_201_CREATED,
        )

    # get lists of objects
    @action(detail=False, methods=["get"], url_path="viewlist")
    def view_list(self, request):
        list_name = request.query_params.get("list_name")
        user_id = request.headers.get("user-id")
        obj_list = ObjectList.objects.get(name=list_name, user_id=user_id)

        if not obj_list:
            return Response(
                {"error": f"No ObjectList found with name '{list_name}'"}, status=404
            )

        results = []

        serialized_objects = ObjectSerializer(obj_list.objects_list.all(), many=True)
        results.append({"list_name": obj_list.name, "objects": serialized_objects.data})

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

    @action(detail=False, methods=["delete"], url_path="delete_obj")
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

    @action(detail=False, methods=["delete"], url_path="delete_list")
    def delete_obj_list(self, request):
        list_name = request.query_params.get("list_name")
        user_id = request.headers.get("user-id")
        obj_list = get_object_or_404(ObjectList, name=list_name, user_id=user_id)
        obj_list.delete()
        return Response(
            {"message": f"object list '{list_name}' deleted"},
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
    @staticmethod
    def _file_cleanup(filename):
        # clean up auto generated files
        remove_file(f"{PROJECT_DIRECTORY}.loc_mgvers.dat")
        remove_file(f"{PROJECT_DIRECTORY}.loc_ociw214.pem")
        remove_file(f"{PROJECT_DIRECTORY}{filename}.obw")

    @staticmethod
    def _get_features(filepath):
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
        return features

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

    def _generate_single_mask(self, user_id, proj_name, data, project):
        filename = data["filename"]

        generate_obj_file(user_id, proj_name, filename, data["objects"])
        generate_obs_file(user_id, proj_name, data, [f"{filename}.obj"])
        os.environ["MGPATH"] = MASKGEN_DIRECTORY
        shutil.copy(
            f"{PROJECT_DIRECTORY}{API_FOLDER}obj_files/{user_id}/{proj_name}/{filename}.obj",
            f"{MASKGEN_DIRECTORY}{filename}.obj",
        )
        shutil.copy(
            f"{PROJECT_DIRECTORY}{API_FOLDER}obs_files/{user_id}/{proj_name}/{filename}.obs",
            f"{MASKGEN_DIRECTORY}{filename}.obs",
        )

        result, feedback = run_maskgen(
            f"{MASKGEN_DIRECTORY}/maskgen -s {filename}.obs",
            data["override"] == "true",
        )
        os.makedirs(
            os.path.join(f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files", user_id),
            exist_ok=True,
        )
        os.makedirs(
            os.path.join(
                f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files", user_id, proj_name
            ),
            exist_ok=True,
        )
        result, feedback = run_maskgen(
            f"{MASKGEN_DIRECTORY}/maskgen -s {filename}.obs",
            data["override"] == "true",
        )
        os.makedirs(
            os.path.join(f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files", user_id),
            exist_ok=True,
        )
        os.makedirs(
            os.path.join(
                f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files", user_id, proj_name
            ),
            exist_ok=True,
        )
        os.rename(
            f"{PROJECT_DIRECTORY}{filename}.SMF",
            f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files/{user_id}/{proj_name}/{filename}.SMF",
        )

        if result and "Writing object file with use counts to" in feedback:
            # process features from SMF
            filepath = os.path.join(
                PROJECT_DIRECTORY,
                API_FOLDER,
                "smf_files",
                user_id,
                proj_name,
                f"{filename}.SMF",
                PROJECT_DIRECTORY,
                API_FOLDER,
                "smf_files",
                user_id,
                proj_name,
                f"{filename}.SMF",
            )
            mask = Mask.objects.create(
                name=filename,
                user_id=user_id,
                status=Status.DRAFT,
                center_ra=data["center_ra"],
                center_dec=data["center_dec"],
                instrument_setup=data,
                instrument_version=InstrumentConfig.objects.filter(
                    instrument=data["instrument"]
                )
                .order_by("-version")
                .first()
                .version,
                features=self._get_features(filepath),
            )

            result, feedback = categorize_objs(
                mask, f"{PROJECT_DIRECTORY}{filename}.obw"
            )
            self._file_cleanup(filename)

            project.masks.add(mask)
            project.save()
            return (
                True,
                Response(
                    {
                        "created": f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files/{user_id}/{proj_name}/{filename}.SMF"
                    },
                    status=status.HTTP_201_CREATED,
                ),
                mask.excluded_obj_list.count(),
            )
        else:
            self._file_cleanup(filename)
            return False, Response(
                {"error": feedback}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"], url_path="generate")
    def generate_masks(self, request):
        data = request.data
        filename = data["filename"]
        proj_name = data["project_name"]
        user_id = request.headers.get("user-id")
        project = Project.objects.get(name=proj_name, user_id=user_id)

        if project.masks.filter(name=filename).exists():
            return Response(
                {"error": "mask name already exists for project"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid, feedback = validate(data)
        if not valid:
            return Response(
                {"error": feedback},
                status=status.HTTP_400_BAD_REQUEST,
            )

        generate_until_all = data.get("generate_until_all_included", False)
        vary_rotator = data.get("vary_rotator_range")
        generated = []
        if vary_rotator:
            for angle in range(
                vary_rotator["start"], vary_rotator["end"] + 1, vary_rotator["step"]
            ):
                data["rotator_angle"] = angle
                data["filename"] = filename + f"_rot{angle}"
                result, response, _ = self._generate_single_mask(
                    self, user_id, proj_name, data, project
                )
                if result:
                    generated.append(data["filename"])
                else:
                    return response
            return Response(
                {"created": generated},
                status=status.HTTP_201_CREATED,
            )
        elif generate_until_all:
            suffix_count = 1
            excluded_count = 1
            while excluded_count > 0:
                data["filename"] = filename + f"_v{suffix_count}"
                result, response, excluded_count = self._generate_single_mask(
                    self, user_id, proj_name, data, project
                )
                if not result:
                    return response
                generated.append(data["filename"])
                suffix_count += 1
            return Response(
                {"created": generated},
                status=status.HTTP_201_CREATED,
            )
        else:
            result, response, _ = self._generate_single_mask(
                user_id, proj_name, data, project
            )
            if result:
                generated.append(data["filename"])
            return response

    @action(detail=False, methods=["post"], url_path="finalize")
    def finalize_mask(self, request):
        data = request.data
        proj_name = data["project_name"]
        user_id = request.headers.get("user-id")
        mask_name = data["mask_name"]
        project = Project.objects.get(name=proj_name, user_id=user_id)
        mask = project.masks.get(name=mask_name)
        if mask:
            mask.status = Status.FINALIZED
            mask.save()
            return Response(
                {"message": "Mask marked as FINALIZED"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "mask does not exist in this project"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["post"], url_path="complete")
    def complete_mask(self, request):
        data = request.data
        proj_name = data["project_name"]
        user_id = request.headers.get("user-id")
        mask_name = data["mask_name"]
        print(user_id, proj_name, mask_name)
        project = Project.objects.get(name=proj_name, user_id=user_id)
        mask = project.masks.get(name=mask_name)
        if mask:
            mask.status = Status.COMPLETED
            mask.save()
            return Response(
                {"message": "Mask marked as COMPLETED"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "mask does not exist in this project"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["post"], url_path="draft")
    def draft_mask(self, request):
        data = request.data
        proj_name = data["project_name"]
        user_id = request.headers.get("user-id")
        mask_name = data["mask_name"]
        print(user_id, proj_name, mask_name)
        project = Project.objects.get(name=proj_name, user_id=user_id)
        mask = project.masks.get(name=mask_name)
        if mask:
            mask.status = Status.DRAFT
            mask.save()
            return Response(
                {"message": "Mask marked as COMPLETED"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "mask does not exist in this project"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        file_paths = [
            f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files/{user_id}/{proj_name}/{mask_name}.SMF",
            f"{PROJECT_DIRECTORY}{API_FOLDER}obs_files/{user_id}/{proj_name}/{mask_name}.obs",
            f"{PROJECT_DIRECTORY}{API_FOLDER}obj_files/{user_id}/{proj_name}/{mask_name}.obj",
            f"{PROJECT_DIRECTORY}{API_FOLDER}nc_files/{user_id}/{proj_name}/I{mask_name}.nc",
        ]
        for file_path in file_paths:
            remove_file(file_path)

        project.masks.remove(mask)
        mask.delete()

        return Response(
            {"message": f"mask '{mask_name}' deleted successfully"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="finalized_masks")
    def get_finalized_masks(self, request):
        """
        Return all masks whose status is FINALIZED
        """
        masks = Mask.objects.filter(status="finalized")
        serializer = MaskSerializer(masks, many=True)
        print(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="completed_masks")
    def get_completed_masks(self, request):
        """
        Return all masks whose status is COMPLETED
        """
        masks = Mask.objects.filter(status="completed")
        serializer = MaskSerializer(masks, many=True)
        print(serializer.data)
        return Response(serializer.data)


class MachineViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="generate")
    def generate_machine_code(self, request):
        data = request.data
        proj_name = data["project_name"]
        print(proj_name)
        print(data)
        user_id = request.headers.get("user-id")
        print(user_id)
        mask_name = data["mask_name"]
        overwrite = data["overwrite"] == "true"
        project = Project.objects.get(name=proj_name, user_id=user_id)
        mask = project.masks.get(name=mask_name)
        if mask.status == Status.FINALIZED:
            os.environ["MGPATH"] = MASKGEN_DIRECTORY
            shutil.copy(
                f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files/{user_id}/{proj_name}/{mask_name}.SMF",
                f"{MASKGEN_DIRECTORY}{mask_name}.SMF",
            )
            result, feedback = run_maskcut(
                f"{MASKGEN_DIRECTORY}/maskcut {mask_name}", overwrite
            )
            print(feedback)
            if result and "Estimated cutting time" in feedback:
                os.makedirs(
                    os.path.join(
                        f"{PROJECT_DIRECTORY}{API_FOLDER}nc_files", user_id, proj_name
                    ),
                    exist_ok=True,
                )
                os.rename(
                    f"{PROJECT_DIRECTORY}I{mask_name}.nc",
                    f"{PROJECT_DIRECTORY}{API_FOLDER}nc_files/{user_id}/{proj_name}/I{mask_name}.nc",
                )

                mask.status = Status.COMPLETED
                return Response(
                    {"created": f"I{mask_name}.nc"},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response({"error": feedback}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                "error, mask has not been marked as completed",
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="get-machine-code")
    def get_machine_code(self, request):
        proj_name = request.query_params.get("project_name")
        mask_name = request.query_params.get("mask_name")
        user_id = request.headers.get("user-id")

        if not all([proj_name, mask_name, user_id]):
            return Response(
                {"error": "missing required query parameters or headers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_path = f"{PROJECT_DIRECTORY}{API_FOLDER}nc_files/{user_id}/{proj_name}/I{mask_name}.nc"

        if os.path.exists(file_path):
            return FileResponse(
                open(file_path, "rb"), content_type="application/x-netcdf"
            )
        else:
            return Response(
                {"error": "Machine code has not been generated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
