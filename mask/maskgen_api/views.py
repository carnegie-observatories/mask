from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
import json
from .serializers import UploadObjectSerializer
from .models import Object, Mask
import pandas as pd

def convert_to_json(filepath):
    if filepath.split(".")[1] == "csv":
        # Read CSV file
        df = pd.read_csv(filepath)

        # DataFrame to JSON
        df.to_json('output.json', orient='records', lines=True)
# Create your views here.
class UploadObjectsView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        uploaded_file_bytes = request.data.get("file").read()
        # Decode from bytes to string
        data_str = uploaded_file_bytes.decode('utf-8')

        # Load JSON string into Python objects (list of dicts)
        data = json.loads(data_str)
        
        created_objects = []
        for row in data:
            a_len = None
            b_len = None
            if 'a_len' in row and row['a_len'] != '':
                a_len = float(row['a_len'])
            if 'b_len' in row and row['b_len'] != '':
                b_len = float(row['b_len'])
            obj = Object.objects.create(
                name=row['name'],
                type=row['type'],
                right_ascension=float(row['ra']),
                declination=float(row['dec']),
                priority=int(row.get('priority', 0)),
                a_len=a_len,
                b_len=b_len,
            )
            created_objects.append(obj.id)

        return Response({"created": created_objects}, status=status.HTTP_201_CREATED)


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
                    "a_len": obj.a_len,
                    "b_len": obj.b_len
                }
                for obj in mask.objects_list.all()
            ]
        })

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