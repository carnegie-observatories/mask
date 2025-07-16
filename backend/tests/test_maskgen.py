from io import BytesIO
from rest_framework.test import APITestCase, APIClient
from maskgen_api.models import Mask, InstrumentConfig, Project
import json
import os

client = APIClient()
TEST_OBJ_FILE_PATH = "/Users/maylinchen/Downloads/mask/backend/tests/data/DCM5V5E.obj"


class MaskViewSetTests(APITestCase):
    def setUp(self):
        self.instrument = "IMACS_sc"
        self.config = InstrumentConfig.objects.create(
            instrument=self.instrument,
            version=1,
            filters={"filter1": "val"},
            dispersers={"disp1": "val"},
            aux=json.dumps({"aux1": "val"}),
        )
        self.test_file_path = os.path.join(
            os.getcwd(), "backend", "tests", "test_files", "instrum_setup_works_ex.json"
        )
        self.maskgen_url = "/api/masks/generate/"

    def test_mask_gen_obj_list(self):
        Project.objects.create(
            name="test", user_id="test", center_ra=1.00, center_dec=1.00
        )
        # create obj file list
        with open(TEST_OBJ_FILE_PATH, "rb") as fh:
            file = BytesIO(fh.read())

        file.name = "DCM5V5E.obj"
        response = client.post(
            "/api/objects/upload/",
            {"file": file, "list_name": "DCM5V5E_obj_1", "project_name": "test"},
            format="multipart",
            **{"HTTP_USER_ID": "test"},
        )

        # upload instrum setup
        with open(self.test_file_path, "r") as f:
            payload = json.load(f)

        response = self.client.post(
            self.maskgen_url,
            data=json.dumps(payload),
            content_type="application/json",
            **{"HTTP_USER_ID": "test"},
        )
        print("Mask Generation Response:", response.status_code, response.data)
        self.assertEqual(response.status_code, 201)
        self.assertIn("created", response.data)
        mask_exists = Mask.objects.filter(name=payload["filename"]).exists()
        self.assertTrue(mask_exists, f"Mask {payload['filename']} not found in DB")
