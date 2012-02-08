from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class Identifier(models.Model):
    name       = models.CharField(max_length=255)
    slug       = models.SlugField()
    authority  = models.ForeignKey('Authority', blank=True, null=True)
    is_primary = models.BooleanField()
    valid_from = models.DateField(blank=True, null=True)
    valid_to   = models.DateField(blank=True, null=True)

    # Identifer can contain a pointer to any model
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    @property
    def url(self):
        if (self.authority is None or self.authority.object_url is None):
            return self.slug
	else:
            return self.authority.object_url % self.slug

    def __unicode__(self):
        return self.name

class IdentifiedModelManager(models.Manager):
    def get_by_identifier(self, identifier, auto_create=False):

        try:
            object = self.get(identifiers__name = identifier)

        except self.model.DoesNotExist:
            if (not auto_create):
                raise
            if ('name' in self.model._meta.get_all_field_names()):
                object = self.create(name = identifier)
            else:
                object = self.create()
            object.identifiers.create(name = identifier, is_primary=True)

        return object

    def filter_by_identifier(self, identifier):
        return self.filter(identifiers__name = identifier)

class IdentifiedModel(models.Model):
    identifiers = generic.GenericRelation(Identifier)
    objects     = IdentifiedModelManager()

    def fallback_identifier(self):
        if hasattr(self, 'name'):
            return self.name
        else:
            return ContentType.objects.get_for_model(self).name

    def __unicode__(self):
        ids = self.identifiers.filter(is_primary=True)
        if (len(ids) > 0):
            return ', '.join(map(str, ids))
        else:
            return self.fallback_identifier()

    class Meta:
        abstract = True

class Authority(models.Model):
    name       = models.CharField(max_length=255)
    homepage   = models.URLField(null=True,blank=True)
    object_url = models.URLField(null=True,blank=True)

    class Meta:
        verbose_name_plural = 'authorities'

    def __unicode__(self):
        return self.name
