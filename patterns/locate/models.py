from django.contrib.gis.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from wq.db.patterns.base import SerializableGenericRelation

from django.conf import settings
SRID = getattr(settings, 'SRID', 4326)


class Location(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    is_primary = models.BooleanField()
    geometry = models.GeometryField(srid=SRID)
    accuracy = models.IntegerField(null=True, blank=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    objects = models.GeoManager()

    def __unicode__(self):
        if self.name is not None and len(self.name) > 0:
            return '%s - %s' % (self.name, self.content_object)
        else:
            return 'Location %s - %s' % (self.pk, self.content_object)

    class Meta:
        db_table = 'wq_location'


class LocatedModel(models.Model):
    locations = SerializableGenericRelation(Location)

    class Meta:
        abstract = True
