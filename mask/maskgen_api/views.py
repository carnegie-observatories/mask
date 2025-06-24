from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
import json
from .serializers import UploadObjectSerializer
from .models import Object, Mask
from .obs_file_formatting import generate_obj_file, generate_obs_file
import pandas as pd
from mask.docker_helper import docker_copy_file_to, docker_run_command, docker_get_file

MASKGEN_CONTAINER_NAME = "maskgen-maskgen-1"

def convert_to_json(filepath):
    if filepath.split(".")[1] == "csv":
        # Read CSV file
        df = pd.read_csv(filepath)

        # DataFrame to JSON
        df.to_json('output.json', orient='records', lines=True)

class UploadObjectsView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        uploaded_file_bytes = request.data.get("file").read()
        # Decode from bytes to string
        data_str = uploaded_file_bytes.decode('utf-8')

        # Load JSON string into Python objects (list of dicts)
        data = json.loads(data_str)
        
        created_objects = []
        for row in data: # switch to pop
            obj, created_object = Object.objects.get_or_create(
                name=row.pop('name'),
                type=row.pop('type'),
                right_ascension=float(row.pop('ra')),
                declination=float(row.pop('dec')),
                priority=int(row.pop('priority')),
                aux=row
            )
            print(created_object)
            created_objects.append(obj.id)

        return Response({"created": created_objects}, status=status.HTTP_201_CREATED)

class ValidateInstrumentSetup(APIView):
    def post(self,request, instument, format=None):
        print(instument)
        return True
    
class UploadInstrumSetup(APIView):
    def post(self, request, format=None):
        data = request.data
        # validator

        # create obj files for objects
        obj_path = generate_obj_file(data['filename'], data['objects'])

        # create obs file
        obs_path = generate_obs_file(data, [obj_path])
        
        # cp files to docker container
        docker_copy_file_to(MASKGEN_CONTAINER_NAME, obj_path, f"app/linux")
        docker_copy_file_to(MASKGEN_CONTAINER_NAME, obs_path, f"app/linux")
        
        # run mask gen and cp .smf to local directory
        docker_run_command(MASKGEN_CONTAINER_NAME, f"maskgen {data['filename']}")

        # use smf to generate a Mask + features + objects (using ids included in the request)
        docker_get_file(MASKGEN_CONTAINER_NAME, f"/masks/{data['filename']}.SMF", "maskgen_api/smf_files")
        return Response({"created": obs_path}, status=status.HTTP_201_CREATED)

class MaskView(APIView):
    def get(self, request, name):
        mask = Mask.objects.get(pk=name)
        return Response({
            "name": name,
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
                } | obj.aux
                for obj in mask.objects_list.all()
            ]
        })

# future
class MakeFeatureView(APIView):
    def post(self, request, name):
        mask = Mask.objects.get(pk=name)
        feature = request.data.copy()
        feature["id"] = len(mask.features) + 1
        mask.features.append(feature)
        # ADD CHECK TO SEE IF SLIT VIOLATES ANY RULES
        mask.save()
        return Response({"message": "Slit created", "slit": feature})
    
class FeatureView(APIView):
    def get(self, request, name, feature_id):
        mask = Mask.objects.get(pk=name)
        for f in mask.features:
            if f.get("id") == feature_id:
                return Response({
                    "slit": f
                })
        return Response({"message": "Slit not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def patch(self, request, name, feature_id):
        mask = Mask.objects.get(pk=name)
        for f in mask.features:
            if f.get("id") == feature_id:
                for key, value in request.data.items():
                    if key != "id":
                        f[key] = value

                mask.save()
                return Response({"message": "feature updated", "feature": f})
        return Response({"message": "feature not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, name, feature_id):
        mask = Mask.objects.get(pk=name)
        new_features = []
        for s in mask.features:
            if s.get("id") != feature_id:
                new_features.append(s)
        mask.features = new_features;
        mask.save()
        return Response({"message": "feature deleted"})