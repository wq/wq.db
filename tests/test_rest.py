from rest_framework.test import APITestCase
from rest_framework import status
import json
from tests.rest_app.models import (
    RootModel, OneToOneModel, ForeignKeyModel, ExtraModel, UserManagedModel,
    Parent, ItemType, GeometryModel, SlugModel, DateModel, ChoiceModel,
)
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured


class RestTestCase(APITestCase):
    def setUp(self):
        instance = RootModel.objects.create(
            slug='instance',
            description="Test",
        )
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
        SlugModel.objects.create(
            code="test",
            name="Test",
        )
        DateModel.objects.create(
            pk=1,
            name="Test",
            date="2015-01-01 12:00Z",
        )
        ChoiceModel.objects.create(
            pk=1,
            name="Test",
            choice="two",
        )

    # Test existence and content of config.json
    def test_rest_config_json(self):
        response = self.client.get('/config.json')
        result = json.loads(response.content.decode('utf-8'))
        self.assertIn("pages", result)

        # Extra config
        self.assertIn("debug", result)

    def test_rest_config_json_rels(self):
        response = self.client.get('/config.json')
        result = json.loads(response.content.decode('utf-8'))
        self.assertIn("pages", result)
        pages = result['pages']
        self.assertIn("parent", pages)
        self.assertIn("children", pages["parent"])
        self.assertEqual(pages['parent']['children'], ["child"])
        self.assertIn("child", pages)
        self.assertIn("parents", pages["child"])
        self.assertEqual(pages['child']['parents'], ["parent"])

    # Test url="" use case
    def test_rest_list_at_root(self):
        response = self.client.get("/.json")
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertTrue(len(response.data['list']) == 1)

    def test_rest_detail_at_root(self):
        response = self.client.get('/instance.json')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertTrue(response.data['description'] == "Test")

    # Test nested models with foreign keys
    def test_rest_detail_nested_foreignkeys(self):
        response = self.client.get('/instance.json')

        # Include explicitly declared serializers for related fields
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

        # Related fields without explicit serializers will not be included
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

    def test_rest_detail_user_serializer(self):
        response = self.client.get('/usermanagedmodels/1.json')
        self.assertIn('user', response.data)
        self.assertIn('label', response.data['user'])
        self.assertNotIn('password', response.data['user'])

    def test_rest_multi(self):
        lists = ['usermanagedmodels', 'items', 'childs']
        response = self.client.get(
            "/multi.json?lists=" + ",".join(lists)
        )
        for listurl in lists:
            self.assertIn(listurl, response.data)
            self.assertIn("list", response.data[listurl])
            self.assertGreater(len(response.data[listurl]["list"]), 0)

    def test_rest_custom_lookup(self):
        response = self.client.get('/slugmodels/test.json')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertEqual(response.data['id'], 'test')

    def test_rest_default_per_page(self):
        response = self.client.get('/parents.json')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertEqual(response.data['per_page'], 50)

    def test_rest_custom_per_page(self):
        response = self.client.get('/childs.json')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertEqual(response.data['per_page'], 100)

    def test_rest_limit(self):
        response = self.client.get('/childs.json?limit=10')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertEqual(response.data['per_page'], 10)

    def test_rest_date_label(self):
        response = self.client.get("/datemodels/1.json")
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertIn('date_label', response.data)
        self.assertEqual(response.data['date_label'], "2015-01-01 06:00 AM")

    def test_rest_choice_label(self):
        response = self.client.get("/choicemodels/1.json")
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertIn('choice_label', response.data)
        self.assertEqual(response.data['choice_label'], "Choice Two")


class RestRouterTestCase(APITestCase):
    def test_rest_model_conflict(self):
        from wq.db import rest
        from tests.conflict_app.models import Item

        # Register model with same name as existing model
        with self.assertRaises(ImproperlyConfigured) as e:
            rest.router.register_model(Item)
        self.assertEqual(
            e.exception.args[0],
            "Could not register <class 'tests.conflict_app.models.Item'>: "
            "the name 'item' was already registered for "
            "<class 'tests.rest_app.models.Item'>"
        )

        # Register model with different name, but same URL as existing model
        with self.assertRaises(ImproperlyConfigured) as e:
            rest.router.register_model(Item, name="conflictitem")
        self.assertEqual(
            e.exception.args[0],
            "Could not register <class 'tests.conflict_app.models.Item'>: "
            "the url 'items' was already registered for "
            "<class 'tests.rest_app.models.Item'>"
        )

        # Register model with different name and URL
        rest.router.register_model(
            Item, name="conflictitem", url="conflictitems"
        )
        self.assertIn("conflictitem", rest.router.get_config()['pages'])


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
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )

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
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )

        # Double-check ORM model & geometry attribute
        obj = GeometryModel.objects.get(id=response.data['id'])
        geom = obj.geometry
        self.assertEqual(geom.srid, 4326)
        self.assertEqual(geom.x, -97)
        self.assertEqual(geom.y, 50)

    def test_rest_date_label_post(self):
        """
        Posting to a model with a date should return a label and an ISO date
        """
        form = {
            'name': "Test Date",
            'date': '2015-06-01 12:00:00Z',
        }
        response = self.client.post("/datemodels.json", form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertIn('date_label', response.data)
        self.assertEqual(response.data['date_label'], "2015-06-01 07:00 AM")
        self.assertIn('date', response.data)
        self.assertEqual(response.data['date'], "2015-06-01T12:00:00Z")

    def test_rest_empty_date_post(self):
        """
        Allow posting an empty date if the field allows nulls
        """
        form = {
            'name': "Test Date",
            'date': '2015-06-01 12:00:00Z',
            'empty_date': '',
        }
        response = self.client.post("/datemodels.json", form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )

    def test_rest_custom_lookup_fk(self):
        RootModel.objects.create(
            slug='test1',
            description='Test #1',
        )
        response = self.client.post('/foreignkeymodels.json', {
            'root_id': 'test1',
        })
        self.assertTrue(status.is_success(response.status_code), response.data)
        rid = response.data.get('id')
        self.assertEqual(response.data, {
            'id': rid,
            'label': 'foreignkeymodel for test1',
            'root_id': 'test1',
            'root_label': 'test1',
        })

        response = self.client.post('/foreignkeymodels.json', {
            'root_id': 'test_invalid',
        })
        self.assertTrue(
            status.is_client_error(response.status_code), response.data
        )
        self.assertEqual(response.data, {
            'root_id': ['Object with slug=test_invalid does not exist.']
        })
