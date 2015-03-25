from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from tests.patterns_app.models import IdentifiedModel
from wq.db.patterns.models import Authority


def ident_by_auth(idents):
    return {
        ident['authority_id']: ident for ident in idents
    }


class IdentifyTestCase(APITestCase):
    def setUp(self):
        self.auth = Authority.objects.create(
            name="Example",
            homepage="http://example.com/",
            object_url="http://example.com/pages/%s",
        )

    def test_identify_find(self):
        instance = IdentifiedModel.objects.find("Test 1")
        self.assertEqual(instance.name, "Test 1")
        self.assertEqual(instance.primary_identifier.name, "Test 1")
        self.assertEqual(instance.primary_identifier.slug, "test-1")

        instance2 = IdentifiedModel.objects.find("Test 1")
        self.assertEqual(instance, instance2)

    def test_identify_auth_url(self):
        instance = IdentifiedModel.objects.find("Test 2")
        instance.identifiers.create(
            authority=self.auth,
            name="Test 2",
            slug="test2"
        )

        ident = instance.primary_identifier
        self.assertIsNone(ident.url)

        ident = instance.identifiers.get(authority=self.auth)
        self.assertEqual(ident.url, "http://example.com/pages/test2")

    def test_identify_order(self):
        auth2 = Authority.objects.create(
            name="Example.org",
            homepage="http://example.org/",
            object_url="http://example.org/content.php?id=%s",
        )
        instance = IdentifiedModel.objects.find("Test 3")
        instance.identifiers.create(
            authority=auth2,
            name="Test 3",
            slug="123",
        )
        instance.identifiers.create(
            authority=self.auth,
            name="Test 3",
            slug="test3"
        )
        idents = list(instance.identifiers.all())
        self.assertIsNone(idents[0].authority)
        self.assertTrue(idents[0].is_primary)
        self.assertEqual(idents[1].authority, self.auth)
        self.assertEqual(idents[2].authority, auth2)


class IdentifyRestTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.auth = Authority.objects.create(
            name="Example",
            homepage="http://example.com/",
            object_url="http://example.com/pages/%s",
        )
        self.instance = IdentifiedModel.objects.find("Test 1")
        self.instance.identifiers.create(
            authority=self.auth,
            name="Test 1",
            slug="test1"
        )
        self.client.force_authenticate(user=self.user)

    def test_identify_post_classic(self):
        form = {
            'name': 'Test 2',
            'identifier--name': "Test 2",
        }
        form['identifier-%s-name' % self.auth.pk] = "Test 2"
        form['identifier-%s-slug' % self.auth.pk] = "test2"
        self.validate_post(form)

    def test_identify_post_jsonform(self):
        form = {
            'name': 'Test 2',

            'identifiers[0][name]': "Test 2",

            'identifiers[1][name]': "Test 2",
            'identifiers[1][authority_id]': self.auth.pk,
            'identifiers[1][slug]': "test2",
        }
        self.validate_post(form)

    def validate_post(self, form):
        response = self.client.post('/identifiedmodels.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['name'], "Test 2")
        self.assertEqual(response.data['id'], "test-2")

        self.assertIn("identifiers", response.data)
        self.assertEqual(len(response.data["identifiers"]), 2)

        idents = ident_by_auth(response.data["identifiers"])

        self.assertEqual(idents[None]["slug"], "test-2")
        self.assertEqual(idents[self.auth.pk]["slug"], "test2")

    def test_identify_put_classic(self):
        form = {
            'name': 'Test 1 - Updated',
            'identifier--name': "Test 1 - Updated",
            'identifier--slug': "test-1-updated",
            'identifier--id': self.instance.primary_identifier.pk
        }
        form['identifier-%s-name' % self.auth.pk] = "Test 1B"
        form['identifier-%s-slug' % self.auth.pk] = "test1b"

        ident = self.instance.identifiers.get(authority=self.auth)
        form['identifier-%s-id' % self.auth.pk] = ident.pk

    def test_identify_put_jsonform(self):
        ident = self.instance.identifiers.get(authority=self.auth)
        form = {
            'name': 'Test 1 - Updated',

            'identifiers[0][id]': self.instance.primary_identifier.pk,
            'identifiers[0][name]': "Test 1 - Updated",
            'identifiers[0][slug]': "test-1-updated",

            'identifiers[1][id]': ident.pk,
            'identifiers[1][name]': "Test 1B",
            'identifiers[1][slug]': "test1b",
            'identifiers[1][type]': self.auth.pk,
        }
        self.validate_put(form)

    def validate_put(self, form):
        url = (
            '/identifiedmodels/%s.json' % self.instance.primary_identifier.slug
        )
        response = self.client.put(url, form)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.instance = IdentifiedModel.objects.get(pk=self.instance.pk)
        self.assertEqual(self.instance.name, "Test 1 - Updated")
        self.assertEqual(response.data['id'], "test-1-updated")

        self.assertIn("identifiers", response.data)
        self.assertEqual(len(response.data["identifiers"]), 2)

        idents = ident_by_auth(response.data["identifiers"])

        self.assertEqual(idents[None]["slug"], "test-1-updated")
        self.assertEqual(idents[self.auth.pk]["slug"], "test1b")
        self.assertEqual(
            idents[self.auth.pk]["url"], "http://example.com/pages/test1b"
        )
