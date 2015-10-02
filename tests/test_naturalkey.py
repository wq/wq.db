from rest_framework.test import APITestCase
from rest_framework import status
from tests.patterns_app.models import (
    NaturalKeyParent, NaturalKeyChild, ModelWithNaturalKey
)
from wq.db.patterns.serializers import NaturalKeySerializer
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

# Tests for natural key models


class NaturalKeyTestCase(APITestCase):
    def test_naturalkey_fields(self):
        # Model APIs
        self.assertEqual(
            NaturalKeyParent.get_natural_key_fields(),
            ['code', 'group']
        )
        self.assertEqual(
            NaturalKeyParent(code='code0', group='group0').natural_key(),
            ['code0', 'group0'],
        )
        self.assertEqual(
            NaturalKeyChild.get_natural_key_fields(),
            ['parent__code', 'parent__group', 'mode']
        )

    def test_naturalkey_create(self):
        # Manager create
        p1 = NaturalKeyParent.objects.create_by_natural_key(
            "code1", "group1"
        )
        self.assertEqual(p1.code, "code1")
        self.assertEqual(p1.group, "group1")

        # get_or_create with same key retrieve existing item
        p2, is_new = NaturalKeyParent.objects.get_or_create_by_natural_key(
            "code1", "group1"
        )
        self.assertFalse(is_new)
        self.assertEqual(p1.pk, p2.pk)

        # Shortcut version
        p3 = NaturalKeyParent.objects.find("code1", "group1")
        self.assertEqual(p1.pk, p3.pk)

    def test_naturalkey_nested_create(self):
        # Manager create, with nested natural key
        c1 = NaturalKeyChild.objects.create_by_natural_key(
            "code2", "group2", "mode1"
        )
        self.assertEqual(c1.parent.code, "code2")
        self.assertEqual(c1.parent.group, "group2")
        self.assertEqual(c1.mode, "mode1")

        # create with same nested key should not create a new parent
        c2 = NaturalKeyChild.objects.create_by_natural_key(
            "code2", "group2", "mode2"
        )
        self.assertEqual(c1.parent.pk, c2.parent.pk)
        self.assertEqual(c2.mode, "mode2")

    def test_naturalkey_duplicate(self):
        # Manager create, with duplicate
        NaturalKeyParent.objects.create_by_natural_key(
            "code1", "group1"
        )
        # create with same key should fail
        with self.assertRaises(IntegrityError):
            NaturalKeyParent.objects.create_by_natural_key(
                "code1", "group1"
            )


class NaturalKeyRestTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_naturalkey_rest_serializer(self):
        # Serializer should include validator
        serializer = NaturalKeySerializer.for_model(NaturalKeyChild)
        self.maxDiff = 10000000
        expect = """
             Serializer():
                 parent = Serializer(required=True):
                     code = CharField(max_length=10, required=True)
                     group = CharField(max_length=10, required=True)
                 mode = CharField(max_length=10, required=True)
                 class Meta:
                     validators = [<NaturalKeyValidator(queryset=NaturalKeyChild.objects.all(), fields=('parent', 'mode'))>]""".replace("             ", "")[1:]  # noqa
        self.assertEqual(str(serializer()), expect)

    def test_naturalkey_rest_post(self):
        # Posting a natural key should work
        form = {
            'mode': 'mode3a',
            'parent[code]': "code3",
            'parent[group]': "group3",
        }
        response = self.client.post('/naturalkeychilds.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['mode'], "mode3a")
        self.assertEqual(response.data['parent']['code'], "code3")
        self.assertEqual(response.data['parent']['group'], "group3")

        # Posting same nested natural key should reuse nested object
        form = {
            'mode': 'mode3b',
            'parent[code]': "code3",
            'parent[group]': "group3",
        }
        response = self.client.post('/naturalkeychilds.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(
            NaturalKeyChild.objects.get(mode='mode3a').parent.pk,
            NaturalKeyChild.objects.get(mode='mode3b').parent.pk,
        )

    def test_naturalkey_rest_duplicate(self):
        # Posting identical natural key should fail
        form = {
            'mode': 'mode3c',
            'parent[code]': "code3",
            'parent[group]': "group3",
        }
        response = self.client.post('/naturalkeychilds.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        form = {
            'mode': 'mode3c',
            'parent[code]': "code3",
            'parent[group]': "group3",
        }
        response = self.client.post('/naturalkeychilds.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data
        )
        self.assertEqual(
            response.data, {
                'non_field_errors': [
                    'The fields parent, mode must make a unique set.'
                ]
            }
        )

    def test_naturalkey_rest_nested_post(self):
        # Posting a regular model with a ref to natural key
        form = {
            'key[mode]': 'mode4',
            'key[parent][code]': "code4",
            'key[parent][group]': "group4",
            'value': 5,
        }
        response = self.client.post('/modelwithnaturalkeys.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['key']['mode'], "mode4")
        self.assertEqual(response.data['key']['parent']['code'], "code4")
        self.assertEqual(response.data['key']['parent']['group'], "group4")

    def test_naturalkey_rest_nested_put(self):
        # Updating a regular model with a ref to natural key
        instance = ModelWithNaturalKey.objects.create(
            key=NaturalKeyChild.objects.find(
                'code5', 'group5', 'mode5'
            ),
            value=7,
        )
        self.assertEqual(instance.key.parent.code, 'code5')

        # Updating with same natural key should reuse it
        form = {
            'key[mode]': 'mode5',
            'key[parent][code]': "code5",
            'key[parent][group]': "group5",
            'value': 8,
        }
        self.assertEqual(
            NaturalKeyChild.objects.count(),
            1
        )

        # Updating with new natural key should create it
        response = self.client.put(
            '/modelwithnaturalkeys/%s.json' % instance.pk, form
        )
        form = {
            'key[mode]': 'mode6',
            'key[parent][code]': "code6",
            'key[parent][group]': "group6",
            'value': 9,
        }
        response = self.client.put(
            '/modelwithnaturalkeys/%s.json' % instance.pk, form
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.assertEqual(response.data['key']['mode'], "mode6")
        self.assertEqual(response.data['key']['parent']['code'], "code6")
        self.assertEqual(response.data['key']['parent']['group'], "group6")
        self.assertEqual(
            NaturalKeyChild.objects.count(),
            2
        )
