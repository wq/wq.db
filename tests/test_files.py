import os

from rest_framework.test import APITestCase
from rest_framework import status

from django.contrib.auth.models import User
from wq.db.patterns.file.models import File


class FilesTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def check_file(self, photo):
        # Width and height should be automatically set for images
        self.assertEqual(photo['is_image'], True)
        self.assertEqual(photo['width'], 1)
        self.assertEqual(photo['height'], 1)
        self.assertEqual(photo['name'], "testimage.png")

        # Use proxy model to set custom upload path
        self.assertIn("photos/testimage", photo['file'])

        # File should not still be open after upload is completed
        instance = File.objects.get(pk=photo['id'])
        self.assertTrue(instance.file.closed)

        # Width and height on images should be set automatically
        self.assertEqual(instance.width, 1)
        self.assertEqual(instance.height, 1)

        # If mimetype parameter is accessed after file is saved, the mimetype
        # should come from the FileType and the actual file should not be
        # read again.
        del instance.file._file
        self.assertEqual(instance.mimetype, "image/png")
        self.assertFalse(hasattr(instance.file, "_file"))

    def test_files_attachment_jsonform(self):
        filename = os.path.join(os.path.dirname(__file__), "testimage.png")
        with open(filename, 'rb') as f:
            response = self.client.post('/photoattachedmodels.json', {
                "name": "Test Photo",
                "files[0][file]": f,
            })
            self.assertTrue(
                status.is_success(response.status_code), response.data
            )
            self.assertEqual(response.data['name'], "Test Photo")
            self.assertIn("files", response.data)
            self.assertEqual(len(response.data['files']), 1)
            self.check_file(response.data['files'][0])

    def test_files_attachment_field(self):
        filename = os.path.join(os.path.dirname(__file__), "testimage.png")
        with open(filename, 'rb') as f:
            response = self.client.post('/photoattachedmodels.json', {
                "name": "Test Photo",
                "files": f,
            })
            self.assertTrue(
                status.is_success(response.status_code), response.data
            )
            self.assertEqual(response.data['name'], "Test Photo")
            self.assertIn("files", response.data)
            self.assertEqual(len(response.data['files']), 1)
            self.check_file(response.data['files'][0])

    def test_files_attachment_multi(self):
        filename1 = os.path.join(os.path.dirname(__file__), "testimage.png")
        filename2 = os.path.join(os.path.dirname(__file__), "version.txt")
        with open(filename1, 'rb') as f1:
            with open(filename2, 'rb') as f2:
                response = self.client.post('/photoattachedmodels.json', {
                    "name": "Test Photo",
                    "files": [f1, f2]
                })
                self.assertTrue(
                    status.is_success(response.status_code), response.data
                )
                self.assertEqual(response.data['name'], "Test Photo")
                self.assertIn("files", response.data)
                self.assertEqual(len(response.data['files']), 2)
                photo = None
                text = None
                for row in response.data['files']:
                    if row['is_image']:
                        photo = row
                    else:
                        text = row
                self.assertEqual(photo['width'], 1)
                self.assertEqual(photo['name'], "testimage.png")
                self.assertIn("photos/testimage", photo['file'])

                self.assertEqual(text['width'], None)
                self.assertEqual(text['name'], "version.txt")
                self.assertIn("photos/version", text['file'])
