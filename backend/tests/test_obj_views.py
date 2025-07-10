import json
import os
import pytest
from io import BytesIO
from rest_framework.test import APIClient
from maskgen_api.models import Object, ObjectList

pytestmark = pytest.mark.django_db  # ensures each test uses a test DB
script_dir = os.path.dirname(__file__)
TEST_OBJ_FILE_PATH = os.path.join(script_dir, "data", "DCM5V5E.obj")
client = APIClient()


@pytest.fixture
def sample_object_data():
    return [
        {
            "name": "a",
            "type": "GUIDE",
            "ra": 10.5,
            "dec": 20.2,
            "priority": 1,
            "extra": "x1",
        },
        {
            "name": "b",
            "type": "TARGET",
            "ra": 30.1,
            "dec": -15.3,
            "priority": 2,
            "meta": "y2",
        },
    ]


def test_upload_objects(sample_object_data):
    list_name = "UploadList"
    json_data = json.dumps(sample_object_data).encode("utf-8")
    file = BytesIO(json_data)
    file.name = "upload.json"

    response = client.post(
        "/api/objects/upload/",
        {"file": file, "list_name": list_name, "user_id": "test"},
        format="multipart",
    )

    assert response.status_code == 201
    assert Object.objects.count() == 2
    obj_list = ObjectList.objects.get(name=list_name)
    assert obj_list.objects_list.count() == 2
    assert response.data["obj_list"] == list_name


def test_upload_objects_from_obj():
    list_name = "UploadList"
    with open(TEST_OBJ_FILE_PATH, "rb") as fh:
        file = BytesIO(fh.read())
    file.name = "upload.obj"

    response = client.post(
        "/api/objects/upload/",
        {"file": file, "list_name": list_name, "user_id": "test"},
        format="multipart",
    )

    assert response.status_code == 201
    assert Object.objects.count() == 1936
    obj_list = ObjectList.objects.get(name=list_name)
    assert obj_list.objects_list.count() == 1936
    assert response.data["obj_list"] == list_name


def test_view_object_list():
    list_name = "ViewList"
    obj1 = Object.objects.create(
        name="obj1", type="ALIGN", right_ascension=1.0, declination=2.0, priority=1
    )
    obj2 = Object.objects.create(
        name="obj2", type="GUIDE", right_ascension=3.0, declination=4.0, priority=2
    )
    obj_list = ObjectList.objects.create(name=list_name)
    obj_list.objects_list.set([obj1, obj2])

    response = client.get(f"/api/objects/viewlist/?list_name={list_name}")

    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 1  # check only one ObjectList was returned

    group = response.data[0]
    assert group["list_name"] == list_name
    assert len(group["objects"]) == 2

    names = [obj["name"] for obj in group["objects"]]
    assert "obj1" in names
    assert "obj2" in names
