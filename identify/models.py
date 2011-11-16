from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib import admin

class IdentifiedModel(models.Model):
    identifiers = generic.GenericRelation('Identifier')

    # Subclasses should override this method
    def fallback_identifier(self):
       return ''

    def __unicode__(self):
       ids = self.identifiers.filter(is_primary=True)
       if (len(ids) > 0):
           return ', '.join(map(str, ids))
       else:
           return self.fallback_identifier()

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

    def __unicode__(self):
      return self.name

class Authority(models.Model):
    name = models.TextField()
    class Meta:
        verbose_name_plural = 'authorities'

    def __unicode__(self):
        return self.name

# Admin interface
class IdentifierInline(generic.GenericTabularInline):
    model = Identifier
    prepopulated_fields = {"slug": ("name",)}

class IdentifiedModelAdmin(admin.ModelAdmin):
    inlines = [
      IdentifierInline,
    ]

admin.site.register(Authority)
