import os

from rest_framework.test import APITestCase
from rest_framework import status

from wq.db.contrib.files.models import File
from django.contrib.auth.models import User


class FilesTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_upload(self):
        filename = os.path.join(os.path.dirname(__file__), "testimage.png")
        with open(filename, 'rb') as f:
            response = self.client.post('/files.json', {"file": f})
            self.assertTrue(
                status.is_success(response.status_code),
                "error uploading file"
            )
            fileid = response.data['id']

            # is_image model/serializer property should be set
            self.assertEqual(response.data['is_image'], True)

        # File should not still be open after upload is completed
        instance = File.objects.get(pk=fileid)
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
