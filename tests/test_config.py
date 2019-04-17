import unittest
from .base import APITestCase
import json
from django.conf import settings


class ConfigTestCase(APITestCase):
    def get_config(self, page_name):
        response = self.client.get('/config.json')
        result = json.loads(response.content.decode('utf-8'))
        self.assertIn('pages', result)
        self.assertIn(page_name, result['pages'])
        return result['pages'][page_name]

    def get_field(self, page_config, field_name, allow_none=False):
        self.assertIn('form', page_config)
        for field in page_config['form']:
            if field['name'] == field_name:
                return field
        if not allow_none:
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
        result = router.get_index(None)
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

    def test_rest_config_json_boolean_choices(self):
        conf = self.get_config('itemtype')
        self.assertEqual([
            {
                'name': 'name',
                'label': 'Name',
                'type': 'string',
                'wq:length': 10,
                'bind': {'required': True},
            },
            {
                'name': 'active',
                'label': 'Active',
                'type': 'select one',
                'choices': [{
                    'name': True,
                    'label': 'Yes',
                }, {
                    'name': False,
                    'label': 'No',
                }],
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

    def test_rest_list_exclude_config(self):
        conf = self.get_config('expensivemodel')
        self.get_field(conf, 'name')
        self.get_field(conf, 'expensive')
        self.assertIsNone(
            self.get_field(conf, 'more_expensive', allow_none=True)
        )
