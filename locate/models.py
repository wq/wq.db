from django.contrib.gis.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class Location(models.Model):
    name       = models.CharField(max_length=255, null=True, blank=True)
    is_primary = models.BooleanField()
    geometry   = models.GeometryField()
    accuracy   = models.IntegerField(null=True, blank=True)

    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey() 

    objects  = models.GeoManager()

    def __unicode__(self):
        if self.name is not None and len(self.name) > 0:
            return '%s - %s'          % (self.name, self.content_object)
        else:
            return 'Location %s - %s' % (self.pk,   self.content_object)

class LocatedModel(models.Model):
    locations = generic.GenericRelation(Location)
    class Meta:
        abstract = True
