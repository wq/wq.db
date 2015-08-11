from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django import forms
from django.conf import settings
import swapper
from wq.db.patterns.models import AnnotatedModel

from wq.io.util import guess_type

swapper.set_app_prefix('files', 'WQ')


# Custom FileField handles both images and files
class FileField(models.ImageField):
    # Use base forms.FileField to skip ImageField validation
    def formfield(self, **kwargs):
        kwargs['form_class'] = forms.FileField
        return super(FileField, self).formfield(**kwargs)

    # Only update_dimension_fields for images
    def update_dimension_fields(self, instance, force=False, *args, **kwargs):
        if (getattr(instance, 'mimetype', None) is not None
                and 'image' in instance.mimetype):
            super(FileField, self).update_dimension_fields(instance, force,
                                                           *args, **kwargs)
        else:
            pass

    # Allow model to specify upload directory
    def generate_filename(self, instance, filename):
        if hasattr(instance, 'get_directory'):
            self.upload_to = instance.get_directory()
        return super(FileField, self).generate_filename(instance, filename)


class FileType(models.Model):
    name = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=255)

    def __str__(self):
        return '%s (%s)' % (self.name, self.mimetype)

    class Meta:
        db_table = 'wq_filetype'


class FileManager(models.Manager):
    def get_queryset(self):
        qs = super(FileManager, self).get_query_set()
        if self.model.type_name is not None:
            return qs.filter(type__name=self.model.type_name)
        else:
            return qs


class BaseFile(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    type = models.ForeignKey(FileType, null=True, blank=True)
    file = FileField(upload_to='.', width_field='width', height_field='height')
    size = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)

    type_name = "File"

    def get_directory(self):
        if self.is_image:
            return 'images'
        else:
            return 'files'

    @property
    def mimetype(self):
        if self.type is not None:
            return self.type.mimetype

        if self.file.name not in (None, ""):
            mimetype = guess_type(self.file.name, self.file.read(1024))
            return mimetype
        else:
            return None

    @property
    def is_image(self):
        return self.mimetype is not None and self.mimetype.startswith('image/')

    def save(self, *args, **kwargs):
        if self.type is None:
            self.type, isnew = FileType.objects.get_or_create(
                mimetype=self.mimetype,
                name=self.type_name
            )
        if self.size is None:
            self.size = self.file.size
        if self.name is None or self.name == '':
            self.name = self.file.name
        super(BaseFile, self).save(*args, **kwargs)

    def __str__(self):
        if self.name is not None:
            return self.name
        else:
            return 'File %s' % self.id

    class Meta:
        abstract = True


class File(BaseFile, AnnotatedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)

    class Meta:
        db_table = 'wq_file'
        ordering = ("name",)
        swappable = swapper.swappable_setting('files', 'File')


class BaseFileAttachment(BaseFile):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey()

    class Meta:
        abstract = True


class FileAttachedModel(models.Model):
    class Meta:
        abstract = True
