from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

import magic

from wq.db.annotate.models import AnnotatedModel
from wq.db.relate.models import RelatedModel

class FileType(models.Model):
    name     = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=255)
    def __unicode__(self):
        return '%s (%s)' % (self.name, self.mimetype)

    class Meta:
        db_table = 'wq_filetype'

class BaseFile(AnnotatedModel, RelatedModel):
    name = models.CharField(max_length=255, null=True, blank=True)     
    type = models.ForeignKey(FileType, null=True, blank=True)

    @property
    def mimetype(self):
        if self.file is not None:
            mime = magic.Magic(mime=True)
            return mime.from_file(self.file.path)
        else:
            return None

    def save(self):
        super(BaseFile, self).save()
        if self.type is not None:
            ftype, isnew = FileType.objects.get_or_create(mimetype=self.mimetype)
            self.type = ftype
            super(BaseFile, self).save()
        if self.name is None or self.name == '':
            udir = self._meta.get_field_by_name('file')[0].upload_to + '/'
            self.name = self.file.name.replace(udir, '')
            super(BaseFile, self).save()

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'wq_basefile'

class File(BaseFile):
    file = models.FileField(upload_to='files')
    class Meta:
        db_table = 'wq_file'

class Image(BaseFile):
    file   = models.ImageField(upload_to='images', width_field='width', height_field='height')
    width  = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = 'wq_image'
