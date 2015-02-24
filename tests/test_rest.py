from rest_framework.test import APITestCase
from rest_framework import status
import json
from tests.rest_app.models import (
    RootModel, OneToOneModel, ForeignKeyModel, ExtraModel, UserManagedModel,
    Parent, Child, ItemType, Item, GeometryModel,
)
from django.contrib.auth.models import User


class RestTestCase(APITestCase):
    def setUp(self):
        instance = RootModel.objects.find('instance')
        instance.description = "Test"
        instance.save()
        for cls in OneToOneModel, ForeignKeyModel, ExtraModel:
            cls.objects.create(
                root=instance,
            )
        user = User.objects.create(username="testuser")
        UserManagedModel.objects.create(id=1, user=user)
        parent = Parent.objects.create(name="Test", pk=1)
        parent.child_set.create(name="Test 1")
        parent.child_set.create(name="Test 2")
        itype = ItemType.objects.create(name="Test", pk=1)
        itype.item_set.create(name="Test 1")
        itype.item_set.create(name="Test 2")

    # Test existence and content of config.json
    def test_rest_config_json(self):
        response = self.client.get('/config.json')
        result = json.loads(response.content.decode('utf-8'))
        self.assertIn("pages", result)

        # Extra config
        self.assertIn("debug", result)

    # Test url="" use case
    def test_rest_list_at_root(self):
        response = self.client.get("/.json")
        self.assertTrue(status.is_success(response.status_code))
        self.assertTrue(len(response.data['list']) == 1)

    def test_rest_detail_at_root(self):
        response = self.client.get('/instance.json')
        self.assertTrue(status.is_success(response.status_code))
        self.assertTrue(response.data['description'] == "Test")

    # Test nested models with foreign keys
    def test_rest_detail_nested_foreignkeys(self):
        response = self.client.get('/instance.json')

        # Include OneToOne fields, and ForeignKeys with related_name=url
        self.assertIn("onetoonemodel", response.data)
        self.assertEqual(
            response.data["onetoonemodel"]["label"],
            "onetoonemodel for instance"
        )
        self.assertIn("extramodels", response.data)
        self.assertEqual(
            response.data["extramodels"][0]["label"],
            "extramodel for instance"
        )

        # ForeignKeys without related_name=url should not be included
        self.assertNotIn("extramodel_set", response.data)
        self.assertNotIn("foreignkeymodel_set", response.data)
        self.assertNotIn("foreignkeymodels", response.data)

    def test_rest_filter_by_parent(self):
        response = self.client.get('/parents/1/childs.json')
        self.assertIn("list", response.data)
        self.assertEqual(len(response.data['list']), 2)

        response = self.client.get('/itemtypes/1/items.json')
        self.assertIn("list", response.data)
        self.assertEqual(len(response.data['list']), 2)

    # Ensure nested serializers are created for SerializableGenericRelations
    # (e.g. identifiers), but only for detail views
    def test_rest_detail_nested_identifiers(self):
        response = self.client.get('/instance.json')
        self.assertIn('identifiers', response.data)
        self.assertEqual(response.data['identifiers'][0]['slug'], 'instance')

    def test_rest_list_nested_identifiers(self):
        response = self.client.get('/.json')
        self.assertNotIn('identifiers', response.data['list'][0])

    def test_rest_detail_user_serializer(self):
        response = self.client.get('/usermanagedmodels/1.json')
        self.assertIn('user', response.data)
        self.assertIn('label', response.data['user'])
        self.assertNotIn('password', response.data['user'])


class RestPostTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser", is_superuser=True)
        self.client.force_authenticate(self.user)

    def test_rest_geometry_post_geojson(self):
        """
        Posting GeoJSON to a model with a geometry field should work.
        """
        form = {
            'name': "Geometry Test 1",
            'geometry': json.dumps({
                "type": "Point",
                "coordinates": [-90, 44]
            })
        }

        # Test for expected response
        response = self.client.post('/geometrymodels.json', form)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Double-check ORM model & geometry attribute
        obj = GeometryModel.objects.get(id=response.data['id'])
        geom = obj.geometry
        self.assertEqual(geom.srid, 4326)
        self.assertEqual(geom.x, -90)
        self.assertEqual(geom.y, 44)

    def test_rest_geometry_post_wkt(self):
        """
        Posting WKT to a model with a geometry field should work.
        """
        form = {
            'name': "Geometry Test 2",
            'geometry': "POINT(%s %s)" % (-97, 50)
        }

        # Test for expected response
        response = self.client.post('/geometrymodels.json', form)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Double-check ORM model & geometry attribute
        obj = GeometryModel.objects.get(id=response.data['id'])
        geom = obj.geometry
        self.assertEqual(geom.srid, 4326)
        self.assertEqual(geom.x, -97)
        self.assertEqual(geom.y, 50)
