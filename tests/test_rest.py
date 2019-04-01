import unittest
from .base import APITestCase
from rest_framework import status
import json
from tests.rest_app.models import (
    RootModel, OneToOneModel, ForeignKeyModel, ExtraModel, UserManagedModel,
    Parent, ItemType, SlugModel, DateModel, ChoiceModel,
)
from tests.gis_app.models import GeometryModel
from tests.rest_app.serializers import (
    ChoiceLabelSerializer, DateLabelSerializer, ItemLabelSerializer,
)
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.urls import include


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
        self.user = User.objects.create(username="testuser")
        UserManagedModel.objects.create(id=1, user=self.user)
        parent = Parent.objects.create(name="Test", pk=1)
        parent.children.create(name="Test 1")
        parent.children.create(name="Test 2")
        parent2 = Parent.objects.create(name="Test 2", pk=2)
        parent2.children.create(name="Test 1")
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

    def get_config(self, page_name):
        response = self.client.get('/config.json')
        result = json.loads(response.content.decode('utf-8'))
        self.assertIn('pages', result)
        self.assertIn(page_name, result['pages'])
        return result['pages'][page_name]

    def get_field(self, page_config, field_name):
        self.assertIn('form', page_config)
        for field in page_config['form']:
            if field['name'] == field_name:
                return field
        self.fail("Could not find %s" % field_name)

    # Test existence and content of config.json
    def test_rest_config_json(self):
        response = self.client.get('/config.json')
        result = json.loads(response.content.decode('utf-8'))
        self.assertIn("pages", result)

        # Extra config
        self.assertIn("debug", result)

    def test_rest_index_json(self):
        from wq.db.rest import router
        result = router.get_index(self.user)
        self.assertIn("pages", result)
        self.assertIn("list", result["pages"][0])
        self.assertNotIn("list", result["pages"][-1])

    def test_rest_config_json_fields(self):
        self.assertEqual([
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'wq:length': 10,
                'bind': {'required': True},
            },
            {
                'name': 'date',
                'label': 'Date',
                'type': 'dateTime',
                'bind': {'required': True},
            },
            {
                'name': 'empty_date',
                'label': 'Empty Date',
                'type': 'dateTime',
            },
        ], self.get_config('datemodel')['form'])

    def test_rest_config_json_choices(self):
        conf = self.get_config('choicemodel')
        self.assertEqual([
            {
                'name': 'name',
                'label': 'Name',
                'hint': 'Enter Name',
                'type': 'string',
                'wq:length': 10,
                'bind': {'required': True},
            },
            {
                'name': 'choice',
                'label': 'Choice',
                'hint': 'Pick One',
                'type': 'select one',
                'bind': {'required': True},
                'choices': [{
                    'name': 'one',
                    'label': 'Choice One',
                }, {
                    'name': 'two',
                    'label': 'Choice Two',
                }, {
                    'name': 'three',
                    'label': 'Choice Three',
                }]
            }
        ], conf['form'])

    def test_rest_config_json_rels(self):
        pconf = self.get_config('parent')
        self.assertEqual({
            'name': 'children',
            'label': 'Children',
            'type': 'repeat',
            'bind': {'required': True},
            'children': [{
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'wq:length': 10,
                'bind': {'required': True},
            }]
        }, self.get_field(pconf, 'children'))

        cconf = self.get_config('child')
        self.assertEqual({
            'name': 'parent',
            'label': 'Parent',
            'type': 'string',
            'wq:ForeignKey': 'parent',
            'bind': {'required': True},
        }, self.get_field(cconf, 'parent'))

    def test_rest_config_json_override(self):
        iconf = self.get_config('item')
        self.assertEqual({
            'name': 'type',
            'label': 'Type',
            'type': 'string',
            'wq:ForeignKey': 'itemtype',
            'filter': {'active':  ['1', '{{#id}}0{{/id}}{{^id}}1{{/id}}']},
            'bind': {'required': True},
        }, self.get_field(iconf, 'type'))

    def test_rest_config_json_label(self):
        pconf = self.get_config('slugrefparent')
        self.assertIn('label_template', pconf)
        self.assertEqual(
            "{{name}}{{#ref_id}} ({{ref}}){{/ref_id}}",
            pconf['label_template'],
        )

    @unittest.skipUnless(settings.WITH_GIS, "requires GIS")
    def test_rest_config_subtype_gis(self):
        conf = self.get_config('geometrymodel')
        field = self.get_field(conf, 'geometry')
        self.assertEqual('geoshape', field['type'])

        conf = self.get_config('pointmodel')
        field = self.get_field(conf, 'geometry')
        self.assertEqual('geopoint', field['type'])

    def test_rest_config_subtype(self):
        conf = self.get_config('filemodel')
        field = self.get_field(conf, 'file')
        self.assertEqual('binary', field['type'])

        conf = self.get_config('imagemodel')
        field = self.get_field(conf, 'image')
        self.assertEqual('image', field['type'])

        conf = self.get_config('item')
        field = self.get_field(conf, 'name')
        self.assertEqual('string', field['type'])

        conf = self.get_config('rootmodel')
        field = self.get_field(conf, 'description')
        self.assertEqual('text', field['type'])

    def test_rest_config_field_order(self):
        conf = self.get_config('slugrefparent')
        self.assertEqual(conf['form'][0]['name'], 'ref')
        self.assertEqual(conf['form'][1]['name'], 'name')

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
        response = self.client.get('/parents/1/children.json')
        self.assertIn("list", response.data)
        self.assertEqual(len(response.data['list']), 2)

        response = self.client.get('/itemtypes/1/items.json')
        self.assertIn("list", response.data)
        self.assertEqual(len(response.data['list']), 2)

    def test_rest_target_to_children(self):
        response = self.client.get('/children-by-parents.json')
        self.assertIn("list", response.data)
        self.assertEqual(len(response.data['list']), 2)
        self.assertIn("target", response.data)
        self.assertEqual(response.data['target'], 'children')

    def test_rest_detail_user_serializer(self):
        response = self.client.get('/usermanagedmodels/1.json')
        self.assertIn('user', response.data)
        self.assertIn('label', response.data['user'])
        self.assertNotIn('password', response.data['user'])

    def test_rest_multi(self):
        lists = ['usermanagedmodels', 'items', 'children']
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
        response = self.client.get('/children.json')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertEqual(response.data['per_page'], 100)

    def test_rest_limit(self):
        response = self.client.get('/children.json?limit=10')
        self.assertTrue(status.is_success(response.status_code), response.data)
        self.assertEqual(response.data['per_page'], 10)

    def test_rest_cache_all(self):
        for num in range(2, 101):
            ItemType.objects.create(
                pk=num,
                name='Type #%s' % num
            )

        tests = [
             (100, '/itemtypes.json'),
             (50, '/itemtypes/'),
             (50, '/itemtypes.json?page=1'),
        ]
        for expect_items, url in tests:
            response = self.client.get(url)
            self.assertTrue(
                status.is_success(response.status_code), response.data
            )
            self.assertEqual(
                len(response.data['list']), expect_items,
                "%s should return %s items" % (url, expect_items)
            )
            self.assertEqual(response.data['pages'], 2)
            self.assertEqual(response.data['per_page'], 50)
            self.assertEqual(response.data['count'], 100)

    def test_rest_cache_filter(self):
        other_user = User.objects.create(username='otheruser')
        UserManagedModel.objects.create(id=2, user=other_user)
        UserManagedModel.objects.create(id=3, user=other_user)

        for auth in False, True:
            if auth:
                self.client.force_authenticate(self.user)

            tests = [
                (3, 1 if auth else 0, '/usermanagedmodels.json'),
                (3, 3, '/usermanagedmodels/'),
                (3, 3, '/usermanagedmodels.json?page=1'),
                (1, 1, '/usermanagedmodels.json?user_id=%s' % self.user.pk),
                (2, 2, '/usermanagedmodels.json?user_id=%s' % other_user.pk),
            ]
            for expect_count, expect_items, url in tests:
                response = self.client.get(url)
                self.assertTrue(
                    status.is_success(response.status_code), response.data
                )
                self.assertEqual(
                    len(response.data['list']), expect_items,
                    "%s should return %s items for %s" % (
                        url, expect_items,
                        "authed user" if auth else "anonymous user"
                    )
                )
                self.assertEqual(response.data['pages'], 1)
                self.assertEqual(response.data['per_page'], 50)
                self.assertEqual(response.data['count'], expect_count)

    def test_rest_cache_none(self):
        tests = [
            (0, '/items.json'),
            (2, '/items/'),
            (2, '/items.json?page=1'),
        ]
        for expect_items, url in tests:
            response = self.client.get(url)
            self.assertTrue(
                status.is_success(response.status_code), response.data
            )
            self.assertEqual(
                len(response.data['list']), expect_items,
                "%s should return %s items" % (url, expect_items)
            )
            self.assertEqual(response.data['pages'], 1)
            self.assertEqual(response.data['per_page'], 50)
            self.assertEqual(response.data['count'], 2)

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

    def test_custom_date_label(self):
        from wq.db.rest import router

        # Default label
        item = DateModel.objects.get(pk=1)
        obj = router.serialize(item)
        self.assertEqual(obj['date_label'], '2015-01-01 06:00 AM')

        # Custom label
        obj = DateLabelSerializer(item).data
        self.assertEqual(obj['date_label'], 'January 1, 2015')

    def test_custom_choice_label(self):
        from wq.db.rest import router

        # Default label
        item = ChoiceModel.objects.get(pk=1)
        obj = router.serialize(item)
        self.assertEqual(obj['choice_label'], 'Choice Two')

        # Custom label
        obj = ChoiceLabelSerializer(item).data
        self.assertEqual(obj['choice_label'], 'TWO')

    def test_custom_fk_label(self):
        from wq.db.rest import router

        # Default labels
        item = ItemType.objects.get(pk=1).item_set.get(name='Test 1')
        obj = router.serialize(item)
        self.assertEqual(obj['type_id'], 1)
        self.assertEqual(obj['type_label'], 'Test')
        self.assertEqual(obj['label'], 'Test 1')

        # Custom labels
        obj = ItemLabelSerializer(item).data
        self.assertEqual(obj['type_id'], 'id-1')
        self.assertEqual(obj['type_label'], 'TEST')
        self.assertEqual(obj['label'], 'Test: Test 1')


class RestRouterTestCase(APITestCase):
    def test_rest_model_conflict(self):
        from wq.db import rest
        from tests.conflict_app.models import Item

        # Register model with same name as existing model
        with self.assertRaises(ImproperlyConfigured) as e:
            rest.router.register_model(Item, fields="__all__")
        self.assertEqual(
            e.exception.args[0],
            "Could not register <class 'tests.conflict_app.models.Item'>: "
            "the name 'item' was already registered for "
            "<class 'tests.rest_app.models.Item'>"
        )
        self.assertNotIn(Item, rest.router._models)

        # Register model with different name, but same URL as existing model
        with self.assertRaises(ImproperlyConfigured) as e:
            rest.router.register_model(
                Item, name="conflictitem", fields="__all__"
            )
        self.assertEqual(
            e.exception.args[0],
            "Could not register <class 'tests.conflict_app.models.Item'>: "
            "the url 'items' was already registered for "
            "<class 'tests.rest_app.models.Item'>"
        )
        self.assertNotIn(Item, rest.router._models)

        # Register model with different name and URL
        rest.router.register_model(
            Item, name="conflictitem", url="conflictitems", fields="__all__"
        )
        self.assertIn(Item, rest.router._models)
        self.assertIn("conflictitem", rest.router.get_config()['pages'])

    def test_rest_old_config(self):
        from wq.db import rest
        from tests.conflict_app.models import TestModel

        with self.assertRaises(ImproperlyConfigured):
            rest.router.register_model(
                TestModel,
                partial=True,
                fields="__all__"
            )

        self.assertNotIn(TestModel, rest.router._models)

        with self.assertRaises(ImproperlyConfigured):
            rest.router.register_model(
                TestModel,
                reversed=True,
                fields="__all__"
            )

        self.assertNotIn(TestModel, rest.router._models)

        with self.assertRaises(ImproperlyConfigured):
            rest.router.register_model(
                TestModel,
                max_local_pages=0,
                fields="__all__"
            )

        self.assertNotIn(TestModel, rest.router._models)

    def test_rest_include(self):
        from wq.db import rest
        include(rest.router.urls)


class RestPostTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser", is_superuser=True)
        self.client.force_authenticate(self.user)

    @unittest.skipUnless(settings.WITH_GIS, "requires GIS")
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

    @unittest.skipUnless(settings.WITH_GIS, "requires GIS")
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
        self.assertEqual(response.data['date'], "2015-06-01T07:00:00-05:00")

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

    def test_rest_empty_string(self):
        def check_result(form, expected_output):
            response = self.client.post("/charfieldmodels.json", form)
            if not expected_output:
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                    response.data
                )
                return

            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, response.data
            )
            for field, value in expected_output.items():
                if value is None:
                    self.assertIsNone(response.data[field])
                else:
                    self.assertEqual(response.data[field], value)

        # No fields submitted
        check_result({}, False)

        # Required field submitted but left blank
        check_result({'required_field': ''}, False)

        # Required field submitted
        check_result({
            'required_field': 'test',
        }, {
            'required_field': 'test',
            'nullable_field': None,
            'blankable_field': '',
            'nullableblankable_field': None,
        })

        # All fields submitted but left blank
        check_result({
            'required_field': 'test',
            'nullable_field': '',
            'blankable_field': '',
            'nullableblankable_field': '',
        }, {
            'required_field': 'test',
            'nullable_field': None,
            'blankable_field': '',
            'nullableblankable_field': '',
        })

    def test_rest_custom_lookup_fk(self):
        SlugModel.objects.create(
            code='test1',
            name='Test #1',
        )
        response = self.client.post('/slugrefparents.json', {
            'ref_id': 'test1',
            'name': "Test FK",
        })
        self.assertTrue(status.is_success(response.status_code), response.data)
        rid = response.data.get('id')
        self.assertEqual(response.data, {
            'id': rid,
            'label': 'Test FK (Test #1)',
            'name': 'Test FK',
            'ref_id': 'test1',
            'ref_label': 'Test #1',
        })

        response = self.client.post('/slugrefparents.json', {
            'ref_id': 'test_invalid',
            'name': "Test FK",
        })
        self.assertTrue(
            status.is_client_error(response.status_code), response.data
        )
        self.assertEqual(response.data, {
            'ref_id': ['Object with code=test_invalid does not exist.']
        })

    def test_rest_list_head(self):
        response = self.client.head('/')
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )

    def test_rest_simpleviewset_head(self):
        response = self.client.head('/login')
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )

    def test_rest_options(self):
        response = self.client.options('/')
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
