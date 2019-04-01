from .base import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
import json
from tests.naturalkey_app.models import ModelWithNaturalKey


class NaturalKeyTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_naturalkey_config(self):
        response = self.client.get('/config.json')
        self.assertEqual([
            {
                'name': 'note',
                'label': 'Note',
                'type': 'text',
                'bind': {'required': True},
            },
            {
                'name': 'key',
                'label': 'Key',
                'type': 'group',
                'bind': {'required': True},
                'children': [{
                     'name': 'parent[slug]',
                     'label': 'Parent',
                     'type': 'string',
                     'wq:ForeignKey': 'naturalkeyparent',
                     'wq:length': 50,
                     'bind': {'required': True},
                }, {
                     'name': 'date',
                     'label': 'Date',
                     'type': 'date',
                     'bind': {'required': True},
                }]
            }
        ], response.data['pages']['modelwithnaturalkey']['form'])

    def test_naturalkey_post(self):
        form = {
            'key[parent][slug]': 'test-key',
            'key[date]': '2016-12-31',
            'note': 'Test Note',
        }

        response = self.client.post('/modelwithnaturalkeys.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        instance = ModelWithNaturalKey.objects.get(pk=response.data['id'])

        self.assertEqual(json.loads(response.content.decode('utf-8')), {
            'id': instance.id,
            'key_id': instance.key_id,

            'note': 'Test Note',
            'key': {
                'parent': {'slug': 'test-key'},
                'date': '2016-12-31',
            },

            'label': 'test-key on 2016-12-31: Test Note',
            'key_label': 'test-key on 2016-12-31',
        })
