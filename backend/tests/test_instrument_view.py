from rest_framework.test import APITestCase
from rest_framework import status
from maskgen_api.models import InstrumentConfig

class InstrumentViewSetTests(APITestCase):
    def setUp(self):
        self.upload_url = "/api/instruments/uploadconfig/"
        self.retrieve_url = "/api/instruments/IMACS_sc/"

    def test_upload_first_config(self):
        """Check if system sets version = 1 properly + upload config"""
        data = {
            "instrument": "IMACS_sc",
            "filters": {"B": "H"},
            "dispersers": {"grism": "IMACS_direct_grism"},
            "aux_ex": "ex"
        }

        response = self.client.post(self.upload_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("created", response.data)

        config = InstrumentConfig.objects.first()
        self.assertEqual(config.version, 1)
        self.assertEqual(config.instrument, "IMACS_sc")

    def test_upload_increment_version(self):
        """Check if system increments config version properly"""
        InstrumentConfig.objects.create(
            instrument="IMACS_sc",
            version=1,
            filters={"R": "filter info here"},
            dispersers={"IMACS_direct_grism": "grism info here"},
            aux={"note": "init"}
        )

        data = {
            "instrument": "IMACS_sc",
            "filters": {"I": "info here"},
            "dispersers": {"grism": "info here"},
            "note": "new version"
        }

        response = self.client.post(self.upload_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        latest = InstrumentConfig.objects.filter(instrument="IMACS_sc").order_by("-version").first()
        self.assertEqual(latest.version, 2)

    def test_retrieve_latest_version(self):
        InstrumentConfig.objects.create(
            instrument="IMACS_sc",
            version=1,
            filters={"R": "info"},
            dispersers={"IMACS_direct_grism": "info"},
            aux={"note": "v1"}
        )
        InstrumentConfig.objects.create(
            instrument="IMACS_sc",
            version=2,
            filters={"I": "info"},
            dispersers={"IMACS_indirect_grism": "hi"},
            aux={"note": "v2"}
        )

        response = self.client.get(self.retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filters"], {"I": "info"})
        self.assertEqual(response.data["dispersers"], {"IMACS_indirect_grism": "hi"})

    def test_retrieve_specific_version(self):
        InstrumentConfig.objects.create(
            instrument="IMACS_sc",
            version=1,
            filters={"R": "info"},
            dispersers={"IMACS_direct_grism": "direct"},
            aux={"note": "v1"}
        )
        InstrumentConfig.objects.create(
            instrument="IMACS_sc",
            version=2,
            filters={"I": "info"},
            dispersers={"IMACS_indirect_grism": "indirect"},
            aux={"note": "v2"}
        )

        response = self.client.get(self.retrieve_url + "?version=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filters"], {"R": "info"})
        self.assertEqual(response.data["dispersers"], {"IMACS_direct_grism": "direct"})
