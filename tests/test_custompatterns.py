from wq.db import rest
from .base import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from tests.patterns_app.models import Campaign, Entity, Attribute


class CustomPatternTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser", is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.campaign1 = Campaign.objects.create(
            slug="test-1",
            name="Test 1",
        )
        self.campaign2 = Campaign.objects.create(
            slug="test-2",
            name="Test 2",
        )
        self.att1 = Attribute.objects.create(
            name="Width",
            is_active=True,
            campaign=self.campaign1,
        )
        self.att2 = Attribute.objects.create(
            name="Height",
            is_active=False,
            campaign=self.campaign1,
        )
        self.att3 = Attribute.objects.create(
            name="Color",
            is_active=True,
            campaign=self.campaign2,
        )
        self.att4 = Attribute.objects.create(
            name="Size",
            is_active=False,
            campaign=self.campaign2,
        )
        self.entity1 = Entity.objects.create(
            name="Test", campaign=self.campaign1
        )

    def test_campaign_config(self):
        response = self.client.get("/config.json")
        self.assertEqual(
            [
                {
                    "name": "slug",
                    "label": "Slug",
                    "type": "string",
                    "bind": {"required": True},
                    "wq:length": 50,
                },
                {
                    "name": "name",
                    "label": "Name",
                    "type": "string",
                    "bind": {"required": True},
                    "wq:length": 10,
                },
                {
                    "name": "attributes",
                    "label": "Attributes",
                    "type": "repeat",
                    "bind": {"required": True},
                    "children": [
                        {
                            "name": "name",
                            "label": "Name",
                            "type": "string",
                            "bind": {"required": True},
                            "wq:length": 10,
                        },
                        {
                            "name": "is_active",
                            "label": "Is Active",
                            "type": "select one",
                            "choices": [
                                {"name": True, "label": "Yes"},
                                {"name": False, "label": "No"},
                            ],
                            "control": {"appearance": "checkbox"},
                        },
                    ],
                },
            ],
            response.data["pages"]["campaign"]["form"],
        )

    def test_eav_config(self):
        response = self.client.get("/config.json")
        self.assertEqual(
            [
                {
                    "name": "campaign",
                    "label": "Campaign",
                    "type": "select one",
                    "wq:ForeignKey": "campaign",
                    "wq:related_name": "entity_set",
                    "bind": {"required": True},
                    "control": {"appearance": "campaign-label"},
                },
                {
                    "name": "general",
                    "label": "Info",
                    "type": "group",
                    "children": [
                        {
                            "name": "name",
                            "label": "Name",
                            "type": "string",
                            "bind": {"required": True},
                            "wq:length": 10,
                        },
                    ],
                    "control": {"appearance": "fieldset"},
                },
                {
                    "name": "values",
                    "label": "Values",
                    "type": "repeat",
                    "bind": {"required": True},
                    "children": [
                        {
                            "name": "attribute",
                            "label": "Attribute",
                            "type": "select one",
                            "wq:ForeignKey": "attribute",
                            "wq:related_name": "value_set",
                            "bind": {"required": True},
                            "control": {"appearance": "attribute-label"},
                        },
                        {
                            "name": "value",
                            "label": "Value",
                            "type": "text",
                            "bind": {"required": True},
                        },
                    ],
                    "control": {"appearance": "eav-fieldset-array"},
                    "initial": {
                        "type_field": "attribute",
                        "filter": {
                            "campaign": "{{campaign_id}}",
                            "is_active": True,
                        },
                    },
                },
            ],
            response.data["pages"]["entity"]["form"],
        )

    def test_campaign_post(self):
        form = {
            "slug": "test-3",
            "name": "Test 3",
            "attributes[0][name]": "Start Temp",
            "attributes[1][name]": "End Temp",
        }

        response = self.client.post("/campaigns.json", form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data["name"], "Test 3")
        self.assertIn("attributes", response.data)
        atts = response.data["attributes"]
        self.assertEqual(len(atts), 2)
        self.assertEqual(atts[0]["name"], "Start Temp")

    def test_campaign_put(self):
        form = {
            "slug": self.campaign1.slug,
            "name": "Test 1'",
            "attributes[0][name]": "Width (ft)",
        }

        response = self.client.put(
            "/campaigns/%s.json" % self.campaign1.slug, form
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.campaign1.refresh_from_db()
        self.assertEqual(self.campaign1.name, "Test 1'")
        self.assertEqual(self.campaign1.attributes.count(), 1)
        self.assertEqual(self.campaign1.attributes.first().name, "Width (ft)")

    def test_eav_post(self):
        form = {
            "campaign_id": self.campaign1.slug,
            "general[name]": "Test A",
            "values[0][attribute_id]": self.att1.pk,
            "values[0][value]": "100",
        }

        response = self.client.post("/entities.json", form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data["general"]["name"], "Test A")
        self.assertIn("values", response.data)
        atts = response.data["values"]
        self.assertEqual(len(atts), 1)
        self.assertEqual(atts[0]["attribute_id"], self.att1.pk)

    def test_eav_post_empty(self):
        form = {
            "campaign_id": self.campaign1.slug,
            "general": {
                "name": "Test B",
            },
            "values": [
                {"value": "", "attribute_id": self.att1.pk},
                {"value": 0, "attribute_id": self.att2.pk},
            ],
        }

        response = self.client.post("/entities.json", form, format="json")
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertIn("values", response.data)
        atts = response.data["values"]
        self.assertEqual(len(atts), 1)
        self.assertEqual(atts[0]["attribute_id"], self.att2.pk)
        self.assertEqual(atts[0]["value"], "0")

    def test_eav_put(self):
        form = {
            "name": "Test'",
            "campaign_id": self.campaign2.slug,
            "values[0][value]": "Red",
            "values[0][attribute_id]": self.att3.pk,
        }

        response = self.client.put("/entities/%s.json" % self.entity1.pk, form)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.entity1.refresh_from_db()
        self.assertEqual(self.entity1.name, "Test'")
        self.assertEqual(self.entity1.values.count(), 1)
        self.assertEqual(self.entity1.values.first().attribute, self.att3)
