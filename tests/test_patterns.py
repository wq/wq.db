from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from tests.patterns_app.models import (
    IdentifiedRelatedModel, IdentifiedMarkedModel,
)
from wq.db.patterns.models import MarkdownType


# Tests for "composite" models combining two patterns
# (individual patterns tests are elsewhere)

class PatternsTestCase(APITestCase):
    def test_identifyrelate_methods(self):
        # Identify methods
        instance1 = IdentifiedRelatedModel.objects.find("Test 1")
        self.assertEqual(instance1.name, "Test 1")
        self.assertEqual(instance1.primary_identifier.slug, "test-1")

        instance2 = IdentifiedRelatedModel.objects.find("Test 2")

        # Relate methods
        instance2.create_relationship(
            instance1,
            name="Parent Of",
            inverse_name="Child Of",
        )
        irels = instance1.inverserelationships.all()
        self.assertEqual(irels.count(), 1)
        self.assertEqual(str(irels[0].reltype), "Child Of")
        self.assertEqual(irels[0].right, instance2)

    def test_identifymark_methods(self):
        # Identify methods
        instance = IdentifiedMarkedModel.objects.find("Test 1")
        self.assertEqual(instance.name, "Test 1")
        self.assertEqual(instance.primary_identifier.slug, "test-1")

        # Mark methods
        marktype = MarkdownType.objects.create(name="en")
        self.assertIsNone(instance.get_html(marktype))
        instance.markdown.create(
            type=marktype,
            markdown="**test**",
        )
        self.assertEqual(
            instance.get_html(marktype),
            "<p><strong>test</strong></p>"
        )


class PatternsRestTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.client.force_authenticate(user=self.user)

        self.parentinstance = IdentifiedRelatedModel.objects.find("Test 1")
        self.childinstance = IdentifiedRelatedModel.objects.find(
            "Test Child 1"
        )
        self.parentinstance.create_relationship(
            self.childinstance,
            name="Parent Of",
            inverse_name="Child Of",
        )
        self.reltype = self.parentinstance.relationships.all()[0].type

        self.marktype = MarkdownType.objects.create(name="en")
        self.markinstance = IdentifiedMarkedModel.objects.find("Test 2")
        self.markinstance.markdown.create(
            type=self.marktype,
            markdown="**Test 2**"
        )

    def test_identifyrelate_post_classic(self):
        form = {
            'name': 'Test 3',
            'identifier--name': "Test 3",
        }
        form['inverserelationship-%s-item_id' % self.reltype.pk] = "test-1"
        self.validate_identifyrelate_post(form)

    def test_identifyrelate_post_jsonform(self):
        form = {
            'name': 'Test 3',
            'identifiers[0][name]': "Test 3",
            'inverserelationships[0][type_id]': self.reltype.pk,
            'inverserelationships[0][item_id]': "test-1",
        }
        self.validate_identifyrelate_post(form)

    def validate_identifyrelate_post(self, form):
        response = self.client.post('/identifiedrelatedmodels.json', form)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Test 3")
        self.assertEqual(response.data['id'], "test-3")

        self.assertIn("identifiers", response.data)
        self.assertEqual(len(response.data["identifiers"]), 1)
        self.assertEqual(response.data['identifiers'][0]['slug'], 'test-3')

        self.assertIn("relationships", response.data)
        self.assertEqual(len(response.data["relationships"]), 0)

        self.assertIn("inverserelationships", response.data)
        irels = response.data['inverserelationships']
        self.assertEqual(len(irels), 1)
        self.assertEqual(irels[0]['item_id'], "test-1")

    def test_identifymark_post_classic(self):
        form = {
            'name': 'Test 4',
            'identifier--name': "Test 4",
        }
        form['markdown-%s-markdown' % self.marktype.pk] = "**test 4**"
        self.validate_identifymark_post(form)

    def test_identifymark_post_jsonform(self):
        form = {
            'name': 'Test 4',
            'identifiers[0][name]': "Test 4",

            'markdown[0][type_id]': self.marktype.pk,
            'markdown[0][markdown]': "**test 4**",
        }
        self.validate_identifymark_post(form)

    def validate_identifymark_post(self, form):
        response = self.client.post('/identifiedmarkedmodels.json', form)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Test 4")
        self.assertEqual(response.data['id'], "test-4")

        self.assertIn("identifiers", response.data)
        self.assertEqual(len(response.data["identifiers"]), 1)
        self.assertEqual(response.data['identifiers'][0]['slug'], 'test-4')

        self.assertIn("markdown", response.data)
        self.assertEqual(len(response.data["markdown"]), 1)
        self.assertEqual(
            response.data['markdown'][0]['html'],
            '<p><strong>test 4</strong></p>',
        )

    def test_identifyrelate_put_classic(self):
        IdentifiedRelatedModel.objects.find("Test Child 2")
        form = {
            'name': 'Test 1 - Updated',
            'identifier--name': "Test 1 - Updated",
            'identifier--slug': "test-1-updated",
            'identifier--id': self.parentinstance.primary_identifier.pk
        }

        form[
            'relationship-%s-id' % self.reltype.pk
        ] = self.parentinstance.relationships.all()[0].pk
        form['relationship-%s-item_id' % self.reltype.pk] = 'test-child-2'
        self.validate_identifyrelate_put(form)

    def test_identifyrelate_put_jsonform(self):
        IdentifiedRelatedModel.objects.find("Test Child 2")
        rel = self.parentinstance.relationships.all()[0]
        ident = self.parentinstance.primary_identifier
        form = {
            'name': 'Test 1 - Updated',

            'identifiers[0][id]': ident.pk,
            'identifiers[0][name]': "Test 1 - Updated",
            'identifiers[0][slug]': "test-1-updated",

            'relationships[0][id]': rel.pk,
            'relationships[0][type_id]': self.reltype.pk,
            'relationships[0][item_id]': 'test-child-2',
        }
        self.validate_identifyrelate_put(form)

    def validate_identifyrelate_put(self, form):
        newchildinstance = IdentifiedRelatedModel.objects.find("Test Child 2")
        url = '/identifiedrelatedmodels/test-1.json'
        response = self.client.put(url, form)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parentinstance = IdentifiedRelatedModel.objects.get(
            pk=self.parentinstance.pk
        )
        self.assertEqual(self.parentinstance.name, "Test 1 - Updated")
        self.assertEqual(response.data['id'], "test-1-updated")

        self.assertIn("identifiers", response.data)
        self.assertEqual(len(response.data["identifiers"]), 1)
        self.assertEqual(
            response.data['identifiers'][0]['slug'],
            "test-1-updated"
        )

        self.assertIn("relationships", response.data)
        rels = response.data['relationships']
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]['item_id'], "test-child-2")

        self.assertEqual(
            newchildinstance.inverserelationships.all()[0].right,
            self.parentinstance,
        )

    def test_identifymark_put_classic(self):
        form = {
            'name': 'Test 2 - Updated',
            'identifier--name': "Test 2 - Updated",
            'identifier--slug': "test-2-updated",
            'identifier--id': self.markinstance.primary_identifier.pk
        }

        form[
            'markdown-%s-id' % self.marktype.pk
        ] = self.markinstance.markdown.all()[0].pk
        form[
            'markdown-%s-markdown' % self.marktype.pk
        ] = '**Test 2 - Updated**'
        self.validate_identifymark_put(form)

    def test_identifymark_put_jsonform(self):
        ident = self.markinstance.primary_identifier
        md = self.markinstance.markdown.all()[0]
        form = {
            'name': 'Test 2 - Updated',

            'identifiers[0][id]': ident.pk,
            'identifiers[0][name]': "Test 2 - Updated",
            'identifiers[0][slug]': "test-2-updated",

            'markdown[0][id]': md.pk,
            'markdown[0][type_id]': self.marktype.pk,
            'markdown[0][markdown]': '**Test 2 - Updated**',
        }
        self.validate_identifymark_put(form)

    def validate_identifymark_put(self, form):
        url = '/identifiedmarkedmodels/test-2.json'
        response = self.client.put(url, form)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.markinstance = IdentifiedMarkedModel.objects.get(
            pk=self.markinstance.pk
        )
        self.assertEqual(self.markinstance.name, "Test 2 - Updated")
        self.assertEqual(response.data['id'], "test-2-updated")

        self.assertIn("identifiers", response.data)
        self.assertEqual(len(response.data["identifiers"]), 1)
        self.assertEqual(
            response.data['identifiers'][0]['slug'],
            "test-2-updated"
        )

        self.assertIn("markdown", response.data)
        mds = response.data['markdown']
        self.assertEqual(len(mds), 1)
        self.assertEqual(
            mds[0]['html'],
            "<p><strong>Test 2 - Updated</strong></p>"
        )
