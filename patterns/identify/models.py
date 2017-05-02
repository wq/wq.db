from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from natural_keys.models import NaturalKeyModelManager, NaturalKeyModel
from ..base.models import LabelModel
from django.template.defaultfilters import slugify
from django.conf import settings
INSTALLED = ('wq.db.patterns.identify' in settings.INSTALLED_APPS)


WQ_IDENTIFIER_ORDER = getattr(
    settings, "WQ_IDENTIFIER_ORDER",
    ["-is_primary", "authority", "name"]
)


def find_unique_slug(name, queryset):
    if not name:
        maxobj = queryset.order_by('-pk').first()
        name = str(maxobj.pk + 1 if maxobj else 1)
    if len(name) > 45:
        name = name[:45]
    slug = slugify(name)
    exists = queryset.filter(slug=slug)
    num = ''
    while exists.count() > 0:
        slug = slugify('%s %s' % (name, num))
        exists = queryset.filter(slug=slug)
        if num == '':
            num = 1
        else:
            num += 1
    return slug


class IdentifierManager(models.Manager):
    def filter_by_identifier(self, identifier):
        return self.filter(
            models.Q(slug=identifier) | models.Q(name=identifier)
        ).order_by('-is_primary')

    def resolve(self, identifiers, exclude_apps=[]):
        resolved = None
        unresolved = None
        for identifier in identifiers:
            ids = self.filter_by_identifier(identifier)
            if exclude_apps:
                ids = ids.exclude(content_type__app_label__in=exclude_apps)
            items = ids.order_by(
                'content_type', 'object_id'
            ).distinct('content_type', 'object_id').count()
            if items == 1:
                if resolved is None:
                    resolved = {}
                resolved[identifier] = ids[0]
            else:
                if unresolved is None:
                    unresolved = {}
                unresolved[identifier] = ids
        return resolved, unresolved

    # Default implementation of get_or_create doesn't work well with generics
    def get_or_create(self, defaults={}, **kwargs):
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            kwargs.update(defaults)
            return self.create(**kwargs), True


class Identifier(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(blank=True)
    authority = models.ForeignKey('Authority', blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    # Identifer can contain a pointer to any model
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    objects = IdentifierManager()

    @property
    def url(self):
        if (not self.authority or not self.authority.object_url):
            return None
        else:
            return self.authority.object_url % self.slug

    def save(self, *args, **kwargs):
        if not self.slug:
            model = self.content_type.model_class()
            queryset = model.objects.exclude(pk=self.object_id)
            self.slug = find_unique_slug(self.name, queryset)

        if self.is_primary and not self.pk:
            exist = self.content_object.primary_identifier
            if exist:
                # Primary identifier already exists for this object, update
                # instead of adding another
                self.pk = exist.pk
                kwargs.pop('force_insert', None)
                kwargs['force_update'] = True

        super(Identifier, self).save(*args, **kwargs)

        if self.is_primary:
            obj = self.content_object
            if self.name != obj.name or self.slug != obj.slug:
                obj.name = self.name
                obj.slug = self.slug
                obj.save()

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'wq_identifier'
        ordering = WQ_IDENTIFIER_ORDER
        abstract = not INSTALLED


class IdentifiedModelManager(NaturalKeyModelManager):
    def get_by_identifier(self, identifier, auto_create=False):
        searches = [
            {'slug': identifier},
            {'name': identifier},
            {'identifiers__slug': identifier},
            {'identifiers__name': identifier},
        ]

        obj = None
        for search in searches:
            try:
                obj = self.get(**search)
                break
            except (ValueError, self.model.DoesNotExist):
                pass

        if obj is None:
            if auto_create:
                obj = self.create_by_natural_key(identifier)
            else:
                name = self.model._meta.object_name
                raise self.model.DoesNotExist(
                    '%s "%s" does not exist' % (name, identifier)
                )

        return obj

    def get_by_natural_key(self, identifier):
        return self.get_by_identifier(identifier)

    def create_by_natural_key(self, identifier):
        return self.create(name=identifier)


class IdentifiedModel(NaturalKeyModel, LabelModel):
    name = models.CharField(
        max_length=255, blank=True, db_index=True
    )
    slug = models.CharField(max_length=255, blank=True, unique=True)

    identifiers = GenericRelation(Identifier)
    objects = IdentifiedModelManager()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = find_unique_slug(self.name, type(self).objects)
        if not self.name:
            self.name = self.slug
        super(IdentifiedModel, self).save()
        ident, is_new = self.identifiers.get_or_create(
            is_primary=True,
            defaults={
                'name': self.name,
                'slug': self.slug,
            }
        )
        if not is_new and (ident.name != self.name or ident.slug != self.slug):
            ident.name = self.name
            ident.slug = self.slug
            ident.save()

    @property
    def primary_identifier(self):
        return self.identifiers.filter(is_primary=True).first()

    class Meta:
        ordering = ['name']
        abstract = True


class Authority(LabelModel):
    name = models.CharField(max_length=255)
    homepage = models.URLField(null=True, blank=True)
    object_url = models.URLField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'authorities'
        db_table = 'wq_identifiertype'
        abstract = not INSTALLED
