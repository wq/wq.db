from wq.db import rest
from .base import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from tests.patterns_app.models import (
    CustomPatternModel,
    CustomTypedPatternModel,
    CustomType,
    Campaign,
    Attribute,
    Entity,
)
from tests.patterns_app.serializers import (
    EntitySerializerBase,
    EntitySerializerCampaignID,
    EntitySerializerIsActiveT,
    EntitySerializerIsActiveF,
    EntitySerializerActiveTCampaignID,
    EntitySerializerCategoryDim,
    EntitySerializerCategoryEmpty,
    EntitySerializerCategoryCtxt,
)


class CustomPatternTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser", is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.type = CustomType.objects.create(
            name="Custom",
        )
        self.instance = CustomPatternModel.objects.create(
            name="Test 1",
        )
        self.typeinstance = CustomTypedPatternModel.objects.create(
            name="Test 2",
        )
        self.campaign1 = Campaign.objects.create()
        self.campaign2 = Campaign.objects.create()
        self.att1 = Attribute.objects.create(
            name="Width",
            is_active=True,
            campaign=self.campaign1,
            category="dimension",
        )
        self.att2 = Attribute.objects.create(
            name="Height",
            is_active=False,
            campaign=self.campaign1,
            category="dimension",
        )
        self.att3 = Attribute.objects.create(
            name="Color",
            is_active=True,
            campaign=self.campaign2,
            category="color",
        )
        self.att4 = Attribute.objects.create(
            name="Size", is_active=False, campaign=self.campaign2, category=""
        )

    def test_customtypedpattern_config(self):
        response = self.client.get("/config.json")
        self.assertEqual(
            [
                {
                    "name": "name",
                    "label": "Name",
                    "type": "string",
                    "bind": {"required": True},
                    "wq:length": 10,
                },
                {
                    "name": "attachments",
                    "label": "Attachments",
                    "type": "repeat",
                    "bind": {"required": True},
                    "children": [
                        {
                            "name": "name",
                            "label": "Name",
                            "type": "string",
                            "wq:length": 10,
                        },
                        {
                            "name": "value",
                            "label": "Value",
                            "type": "decimal",
                        },
                        {
                            "name": "type",
                            "label": "Type",
                            "type": "select one",
                            "wq:ForeignKey": "customtype",
                            "wq:related_name": "customtypedattachment_set",
                            "bind": {"required": True},
                        },
                    ],
                    "initial": {"type_field": "type", "filter": {}},
                },
            ],
            response.data["pages"]["customtypedpatternmodel"]["form"],
        )

    def test_custompattern_post(self):
        form = {
            "name": "Test 3",
            "attachments[0][name]": "Attachment",
            "attachments[1][name]": "Attachment",
        }

        response = self.client.post("/custompatternmodels.json", form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data["name"], "Test 3")
        self.assertIn("attachments", response.data)
        atts = response.data["attachments"]
        self.assertEqual(len(atts), 2)
        self.assertEqual(atts[0]["name"], "Attachment")

    def test_custompattern_put(self):
        form = {"name": "Test 1'", "attachments[0][name]": "Attachment"}

        response = self.client.put(
            "/custompatternmodels/%s.json" % self.instance.pk, form
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.instance = CustomPatternModel.objects.get(pk=self.instance.pk)
        self.assertEqual(self.instance.name, "Test 1'")
        self.assertEqual(self.instance.attachments.count(), 1)
        self.assertEqual(self.instance.attachments.first().name, "Attachment")

    def test_customtypedpattern_post(self):
        form = {
            "name": "Test 4",
            "attachments[0][name]": "Attachment",
            "attachments[0][type_id]": self.type.pk,
        }

        response = self.client.post("/customtypedpatternmodels.json", form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data["name"], "Test 4")
        self.assertIn("attachments", response.data)
        atts = response.data["attachments"]
        self.assertEqual(len(atts), 1)
        self.assertEqual(atts[0]["type_label"], "Custom")

    def test_customtypedpattern_post_empty(self):
        form = {
            "name": "Test 5",
            "attachments": [
                {"value": "", "type_id": self.type.pk, "name": ""},
                {"value": 0, "type_id": self.type.pk, "name": ""},
            ],
        }

        response = self.client.post(
            "/customtypedpatternmodels.json", form, format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertIn("attachments", response.data)
        atts = response.data["attachments"]
        self.assertEqual(len(atts), 1)
        self.assertEqual(atts[0]["type_label"], "Custom")
        self.assertEqual(atts[0]["value"], 0)

    def test_customtypedpattern_put(self):
        form = {
            "name": "Test 2'",
            "attachments[0][name]": "Attachment",
            "attachments[0][type_id]": self.type.pk,
        }

        response = self.client.put(
            "/customtypedpatternmodels/%s.json" % self.typeinstance.pk, form
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.typeinstance = CustomTypedPatternModel.objects.get(
            pk=self.typeinstance.pk
        )
        self.assertEqual(self.typeinstance.name, "Test 2'")
        self.assertEqual(self.typeinstance.attachments.count(), 1)
        self.assertEqual(self.typeinstance.attachments.first().type, self.type)
