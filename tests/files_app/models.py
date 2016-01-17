from django.db import models
from wq.db.patterns.file.models import File, FiledModel


class Photo(File):
    def get_directory(self):
        return "photos"

    class Meta:
        proxy = True


class PhotoAttachedModel(FiledModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
