from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from tests.patterns_app.models import AnnotatedModel
from wq.db.patterns.models import AnnotationType, Annotation


def value_by_type(attachments):
    return {
        a['type_id']: a['value'] for a in attachments
    }


class AnnotateTestCase(APITestCase):
    def setUp(self):
        AnnotationType.objects.create(name="Width")
        AnnotationType.objects.create(name="Height")

    def test_annotate_simple(self):
        instance = AnnotatedModel.objects.create(name="Test")
        instance.vals = {
            "Width": 200,
            "Height": 200
        }
        self.assertEqual(instance.annotations.count(), 2)
        annotations = Annotation.objects.filter(
            object_id=instance.pk
        )
        self.assertEqual(annotations.count(), 2)

    def test_annotate_invalid_type(self):
        instance = AnnotatedModel.objects.create(name="Test")
        with self.assertRaises(TypeError):
            instance.vals = {
                "Invalid Annotation Type": "Test",
            }


class AnnotateRestTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.width = AnnotationType.objects.create(
            name="Width",
        )
        self.height = AnnotationType.objects.create(
            name="Height",
        )
        self.instance = AnnotatedModel.objects.create(name="Test 1")
        self.instance.vals = {
            'Width': 200,
            'Height': 200
        }
        self.client.force_authenticate(user=self.user)

    def test_annotate_post_classic(self):
        form = {
            'name': 'Test 2'
        }
        form['annotation-%s-value' % self.width.pk] = 350
        form['annotation-%s-value' % self.height.pk] = 400
        self.validate_post(form)

    def test_annotate_post_jsonform(self):
        form = {
            'name': 'Test 2',

            'annotations[0][type_id]': self.width.pk,
            'annotations[0][value]': 350,

            'annotations[1][type_id]': self.height.pk,
            'annotations[1][value]': 400,
        }
        self.validate_post(form)

    def validate_post(self, form):
        response = self.client.post('/annotatedmodels.json', form)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data
        )
        self.assertEqual(response.data['name'], "Test 2")
        self.assertIn("annotations", response.data)
        self.assertEqual(len(response.data["annotations"]), 2)
        values = value_by_type(response.data['annotations'])
        self.assertEqual(values[self.width.pk], '350')
        self.assertEqual(values[self.height.pk], '400')

    def test_annotate_put_classic(self):
        form = {
            'name': 'Test 1 - Updated'
        }
        for aname in 'width', 'height':
            atype = getattr(self, aname)
            prefix = 'annotation-%s-' % atype.pk
            form[prefix + 'id'] = self.instance.annotations.get(type=atype).pk
            form[prefix + 'value'] = 600

        self.validate_put(form)

    def test_annotate_put_jsonform(self):
        form = {
            'name': 'Test 1 - Updated'
        }
        for i, aname in enumerate(['width', 'height']):
            atype = getattr(self, aname)
            annot = self.instance.annotations.get(type=atype)
            prefix = 'annotations[%s]' % i
            form[prefix + '[id]'] = annot.pk
            form[prefix + '[type_id]'] = atype.pk
            form[prefix + '[value]'] = 600
        self.validate_put(form)

    def validate_put(self, form):
        response = self.client.put(
            '/annotatedmodels/%s.json' % self.instance.pk,
            form
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data
        )
        self.instance = AnnotatedModel.objects.get(pk=self.instance.pk)
        self.assertEqual(self.instance.name, "Test 1 - Updated")
        self.assertIn("annotations", response.data)
        self.assertEqual(len(response.data["annotations"]), 2)
        values = value_by_type(response.data['annotations'])
        for aname in 'width', 'height':
            atype = getattr(self, aname)
            self.assertEqual(values[atype.pk], '600')
            self.assertEqual(
                self.instance.annotations.get(type=atype).value,
                '600'
            )

    def test_annotate_list(self):
        response = self.client.get('/annotations.json')
        for row in response.data['list']:
            self.assertIn('annotatedmodel_id', row)
            self.assertEqual(row['annotatedmodel_id'], self.instance.pk)
            self.assertNotIn('annotatedmodel', row)

    def test_annotate_detail(self):
        annot = self.instance.annotations.all()[0]
        response = self.client.get('/annotations/%s.json' % annot.pk)
        self.assertIn('annotatedmodel', response.data)
        data = response.data['annotatedmodel']
        self.assertEqual(data['id'], self.instance.pk)
        self.assertEqual(data['label'], str(self.instance))
