from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from tests.patterns_app.models import (
    CustomPatternModel, CustomTypedPatternModel, CustomType
)


class CustomPatternTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_superuser=True)
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

    def test_custompattern_post(self):
        form = {
            'name': 'Test 3',

            'attachments[0][name]': 'Attachment',
            'attachments[1][name]': 'Attachment',
        }

        response = self.client.post('/custompatternmodels.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['name'], "Test 3")
        self.assertIn("attachments", response.data)
        atts = response.data['attachments']
        self.assertEqual(len(atts), 2)
        self.assertEqual(atts[0]['name'], 'Attachment')

    def test_custompattern_put(self):
        form = {
            'name': "Test 1'",
            'attachments[0][name]': "Attachment"
        }

        response = self.client.put(
            '/custompatternmodels/%s.json' % self.instance.pk,
            form
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
            'name': 'Test 4',
            'attachments[0][name]': 'Attachment',
            'attachments[0][type_id]': self.type.pk,
        }

        response = self.client.post('/customtypedpatternmodels.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['name'], "Test 4")
        self.assertIn("attachments", response.data)
        atts = response.data['attachments']
        self.assertEqual(len(atts), 1)
        self.assertEqual(atts[0]['type_label'], 'Custom')

    def test_customtypedpattern_put(self):
        form = {
            'name': "Test 2'",
            'attachments[0][name]': "Attachment",
            'attachments[0][type_id]': self.type.pk,
        }

        response = self.client.put(
            '/customtypedpatternmodels/%s.json' % self.typeinstance.pk,
            form
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.typeinstance = CustomTypedPatternModel.objects.get(
            pk=self.typeinstance.pk
        )
        self.assertEqual(self.typeinstance.name, "Test 2'")
        self.assertEqual(self.typeinstance.attachments.count(), 1)
        self.assertEqual(
            self.typeinstance.attachments.first().type, self.type
        )
