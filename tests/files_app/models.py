from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from wq.db.contrib.files.models import BaseFileAttachment, FileAttachedModel


class Photo(BaseFileAttachment):
    def get_directory(self):
        return "photos"


class PhotoAttachedModel(FileAttachedModel):
    name = models.CharField(max_length=255)
    photos = GenericRelation(Photo)

    def __str__(self):
        return self.name
