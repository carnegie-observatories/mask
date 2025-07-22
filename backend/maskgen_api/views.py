# maskgen_api/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import FileResponse

from astropy.table import Table

from .models import Object, Mask, ObjectList, InstrumentConfig, Status, Project, Image
from .serializers import ObjectSerializer
from .obs_file_formatting import (
    generate_obj_file,
    generate_obs_file,
    obj_to_json,
    categorize_objs,
    to_deg,
)
from backend.terminal_helper import run_command, run_maskgen, remove_file

import json
import os
import re
import io

MASKGEN_DIRECTORY = "/Users/maylinchen/downloads/maskgen-2.14-Darwin-12.6_arm64/"
PROJECT_DIRECTORY = os.getcwd() + "/"
API_FOLDER = "maskgen_api/"


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


class ImageViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["get"], url_path="getimg")
    def get_image(self, request):
        user_id = request.headers.get("user-id")
        img_name = request.query_params.get("img_name")
        proj_name = request.query_params.get("project_name")
        print(proj_name)
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
            with open("output.json", "w") as f:
                json.dump(data, f, indent=2)
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

        obj_list = ObjectList.objects.create(name=list_name, user_id=user_id)
        created_objects = []

        for row in data:
            # convert hours to degs if in hrs
            ra, dec = to_deg(row.pop("ra"), row.pop("dec"))

            obj, _ = Object.objects.get_or_create(
                name=row.pop("name"),
                user_id=request.headers.get("user-id"),
                defaults={
                    "type": row.pop("type"),
                    "right_ascension": ra,
                    "declination": dec,
                    "priority": int(row.pop("priority")),
                    "aux": row,
                },
            )
            created_objects.append(obj.id)
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

    # TODO: delete obj


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
        print(proj_name, user_id)
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

    @action(detail=False, methods=["post"], url_path="generate")
    def generate_mask(self, request):
        data = request.data
        filename = data["filename"]
        proj_name = data["project_name"]
        generate_obj_file(filename, data["objects"])
        generate_obs_file(data, [f"{filename}.obj"])
        os.environ["MGPATH"] = MASKGEN_DIRECTORY

        run_command(
            f"cp {PROJECT_DIRECTORY}{API_FOLDER}obj_files/{filename}.obj {MASKGEN_DIRECTORY}"
        )
        run_command(
            f"cp {PROJECT_DIRECTORY}{API_FOLDER}obs_files/{filename}.obs {MASKGEN_DIRECTORY}"
        )
        result, feedback = run_maskgen(f"{MASKGEN_DIRECTORY}/maskgen -s {filename}.obs")

        run_command(
            f"mv {PROJECT_DIRECTORY}{filename}.SMF {PROJECT_DIRECTORY}{API_FOLDER}smf_files"
        )
        if result and "Writing object file with use counts to" in feedback:
            # process features from SMF
            filepath = os.path.join(
                PROJECT_DIRECTORY, API_FOLDER, "smf_files", f"{filename}.SMF"
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
                features=self._get_features(filepath),
            )

            result, feedback = categorize_objs(
                mask, f"{PROJECT_DIRECTORY}{filename}.obw"
            )
            self._file_cleanup(filename)
            project = Project.objects.get(
                name=proj_name, user_id=request.headers.get("user-id")
            )
            project.masks.add(mask)
            project.save()

            return Response(
                {"created": f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files/{filename}.SMF"},
                status=status.HTTP_201_CREATED,
            )
        else:
            self._file_cleanup(filename)
            pattern_with_error = r"""
            (?<=\n)
            (?:
                \s*\*\*.*?\*\*\s*\n       # lines starting and ending with "**"
            )+
            """
            matches = re.findall(
                pattern_with_error, feedback, re.MULTILINE | re.VERBOSE
            )
            error_block = matches[0] if matches else ""
            clean_lines = [line.strip(" *") for line in error_block.splitlines()]
            cleaned = [s for s in clean_lines if re.search(r"[a-zA-Z]", s)]
            if len(cleaned) != 0:
                return Response({"error": cleaned}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": feedback}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="complete")
    def complete_mask(self, request):
        data = request.data
        proj_name = data["project_name"]
        user_id = request.headers.get("user-id")
        mask_name = data["mask_name"]
        project = Project.objects.get(name=proj_name, user_id=user_id)
        mask = project.masks.get(name=mask_name)
        if mask:
            mask.status = Status.COMPLETED
            mask.save()
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
            f"{PROJECT_DIRECTORY}{API_FOLDER}smf_files/{mask_name}.SMF",
            f"{PROJECT_DIRECTORY}{API_FOLDER}obs_files/{mask_name}.obs",
            f"{PROJECT_DIRECTORY}{API_FOLDER}obj_files/{mask_name}.obj",
            f"{PROJECT_DIRECTORY}{API_FOLDER}nc_files/I{mask_name}.nc",
        ]
        for file_path in file_paths:
            remove_file(file_path)

        project.masks.remove(mask)
        mask.delete()

        return Response(
            {"message": f"mask '{mask_name}' deleted successfully"},
            status=status.HTTP_200_OK,
        )


class MachineViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], url_path="generate")
    def generate_machine_code(self, request):
        data = request.data
        proj_name = data["project_name"]
        user_id = request.headers.get("user-id")
        mask_name = data["mask_name"]
        project = Project.objects.get(name=proj_name, user_id=user_id)
        mask = project.masks.get(name=mask_name)
        if mask.status == Status.COMPLETED:
            os.environ["MGPATH"] = MASKGEN_DIRECTORY
            run_command(
                f"cp {PROJECT_DIRECTORY}{API_FOLDER}smf_files/{mask_name}.SMF {MASKGEN_DIRECTORY}"
            )
            result, feedback = run_maskgen(f"{MASKGEN_DIRECTORY}/maskcut {mask_name}")
            if result and "Estimated cutting time" in feedback:
                remove_file(f"{MASKGEN_DIRECTORY}{mask_name}.SMF")
                run_command(
                    f"mv {PROJECT_DIRECTORY}I{mask_name}.nc {PROJECT_DIRECTORY}{API_FOLDER}nc_files"
                )

                mask.status = Status.FINALIZED
                return Response(
                    {"created": f"l{mask_name}.nc"},
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
        data = request.data
        proj_name = data["project_name"]
        user_id = request.headers.get("user-id")
        mask_name = data["mask_name"]
        project = Project.objects.get(name=proj_name, user_id=user_id)
        mask = project.masks.get(name=mask_name)
        if mask.status == Status.FINALIZED:
            file_path = f"{PROJECT_DIRECTORY}nc_files/I{mask_name}.nc"
            return FileResponse(
                open(file_path, "rb"), content_type="application/x-netcdf"
            )
