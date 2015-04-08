from django.contrib.gis.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)

from django.conf import settings
SRID = getattr(settings, 'SRID', 4326)
INSTALLED = ('wq.db.patterns.locate' in settings.INSTALLED_APPS)


class Location(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    geometry = models.GeometryField(srid=SRID)
    accuracy = models.IntegerField(null=True, blank=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    objects = models.GeoManager()

    def __str__(self):
        if self.name is not None and len(self.name) > 0:
            return '%s - %s' % (self.name, self.content_object)
        else:
            return 'Location %s - %s' % (self.pk, self.content_object)

    class Meta:
        db_table = 'wq_location'
        abstract = not INSTALLED


class LocatedModel(models.Model):
    locations = GenericRelation(Location)

    class Meta:
        abstract = True
