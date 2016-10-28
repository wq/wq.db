from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from ..base.models import LabelModel
from django.db.models.query_utils import PathInfo
from django.conf import settings

INSTALLED = ('wq.db.patterns.relate' in settings.INSTALLED_APPS)


class GenericRelation(GenericRelation):
    def get_path_info(self):
        """
        Django 1.10 will try to resolve InverseRelationship to Relationship;
        that check is not needed in this case.
        """
        if not hasattr(self, 'remote_field'):
            return super(GenericRelation, self).get_path_info()

        opts = self.remote_field.model._meta
        target = opts.pk
        return [PathInfo(
            self.model._meta,
            opts,
            (target,),
            self.remote_field,
            True,
            False
        )]


class RelatedModelManager(models.Manager):
    def filter_by_related(self, *args, **kwargs):
        objects = {}
        for obj in args:
            ctype = ContentType.objects.get_for_model(obj)
            if ctype not in objects:
                objects[ctype] = []
            objects[ctype].append(obj)

        data = self.all()
        for ctype, objs in objects.items():
            ids = [obj.pk for obj in objs]
            if kwargs.get('inverse', False):
                data = data.filter(
                    relationships__to_content_type=ctype,
                    relationships__to_object_id__in=ids,
                )
            else:
                data = data.filter(
                    inverserelationships__from_content_type=ctype,
                    inverserelationships__from_object_id__in=ids,
                )
        return data


class RelationshipManager(models.Manager):
    def create_relationship(self, from_obj, to_obj, name,
                            inverse_name=None, computed=False):
        from_ct = ContentType.objects.get_for_model(from_obj)
        to_ct = ContentType.objects.get_for_model(to_obj)
        reltype, is_new = RelationshipType.objects.get_or_create(
            from_type=from_ct,
            to_type=to_ct,
            name=name,
            inverse_name=inverse_name,
            computed=computed,
        )
        rel, is_new = self.get_or_create(
            type=reltype,
            from_content_type=from_ct,
            from_object_id=from_obj.pk,
            to_content_type=to_ct,
            to_object_id=to_obj.pk,
            computed=computed,
        )
        return rel


class Relationship(models.Model):

    type = models.ForeignKey('RelationshipType')

    # Objects can contain pointers to any model
    from_content_type = models.ForeignKey(ContentType, related_name='+')
    from_object_id = models.PositiveIntegerField()
    from_content_object = GenericForeignKey(
        'from_content_type', 'from_object_id'
    )

    to_content_type = models.ForeignKey(ContentType, related_name='+')
    to_object_id = models.PositiveIntegerField()
    to_content_object = GenericForeignKey(
        'to_content_type', 'to_object_id'
    )

    computed = models.BooleanField(default=False)

    objects = RelationshipManager()

    _dict_cache = {}
    _cache_prefix = 'rel'

    @property
    def left(self):
        return self.from_content_object

    @property
    def right(self):
        return self.to_content_object

    @right.setter
    def right(self, value):
        self.to_content_object = value

    @property
    def right_object_id(self):
        return self.to_object_id

    @property
    def right_content_type_id(self):
        return self.to_content_type_id

    @property
    def reltype(self):
        return RelationshipType.objects.get_type(self.type_id)

    @property
    def right_dict(self):
        key = self._cache_prefix + str(self.pk)
        cache = type(self)._dict_cache
        if key not in cache:
            from wq.db.rest.models import get_object_id, get_ct
            obj = self.right
            oid = get_object_id(obj)
            ct = get_ct(obj)
            cache[key] = {
                'item_id': get_object_id(obj),
                'item_label': str(obj),
                'item_url': '%s/%s' % (ct.urlbase, oid),
                'item_page': ct.identifier
            }
        return cache[key]

    def _reset_dict_cache(self):
        for cls in Relationship, InverseRelationship:
            key = cls._cache_prefix + str(self.pk)
            if key in cls._dict_cache:
                del cls._dict_cache[key]

    def save(self, *args, **kwargs):
        rightct = self.reltype.right
        self.right = rightct.get_object_for_this_type(pk=self.right_object_id)
        super(Relationship, self).save(*args, **kwargs)
        self._reset_dict_cache()

    def __str__(self):
        if (self.from_content_type_id and self.type_id and
                self.to_content_type_id):
            return '%s %s %s' % (self.left, self.reltype, self.right)
        else:
            return 'Undefined'

    class Meta:
        db_table = 'wq_relationship'
        abstract = not INSTALLED


class InverseRelationshipManager(models.Manager):
    def get_queryset(self):
        qs = super(InverseRelationshipManager, self).get_queryset()
        return qs.filter(type__inverse_name__isnull=False)


class InverseRelationship(Relationship):
    objects = InverseRelationshipManager()
    _cache_prefix = 'inv'

    @property
    def left(self):
        return self.to_content_object

    @property
    def right(self):
        return self.from_content_object

    @right.setter
    def right(self, value):
        self.from_content_object = value

    @property
    def right_object_id(self):
        return self.from_object_id

    @property
    def right_content_type_id(self):
        return self.from_content_type_id

    @property
    def reltype(self):
        return InverseRelationshipType.objects.get_type(self.type_id)

    class Meta:
        proxy = INSTALLED
        abstract = not INSTALLED


class RelatedModel(models.Model):
    relationships = GenericRelation(
        Relationship,
        content_type_field='from_content_type',
        object_id_field='from_object_id',
    )
    inverserelationships = GenericRelation(
        InverseRelationship,
        content_type_field='to_content_type',
        object_id_field='to_object_id',
    )
    objects = RelatedModelManager()

    def all_relationships(self):
        for rel in self.relationships.all():
            yield rel
        for rel in self.inverserelationships.all():
            yield rel

    def create_relationship(self, to_obj, name,
                            inverse_name=None, computed=False):
        return Relationship.objects.create_relationship(
            from_obj=self,
            to_obj=to_obj,
            name=name,
            inverse_name=inverse_name,
            computed=computed
        )

    class Meta:
        abstract = True


class RelationshipTypeManager(models.Manager):
    _type_cache = {}
    _cache_prefix = 'rel'

    def get_type(self, pk):
        key = self._cache_prefix + str(pk)
        cache = type(self)._type_cache
        if key not in cache:
            cache[key] = self.get(pk=pk)
        return cache[key]


class RelationshipType(LabelModel):
    name = models.CharField(max_length=255)
    inverse_name = models.CharField(max_length=255, null=True, blank=True)

    from_type = models.ForeignKey(ContentType, related_name='+')
    to_type = models.ForeignKey(ContentType, related_name='+')

    computed = models.BooleanField(default=False)

    objects = RelationshipTypeManager()

    @property
    def left(self):
        return self.from_type

    @property
    def right(self):
        return self.to_type

    class Meta:
        db_table = 'wq_relationshiptype'
        abstract = not INSTALLED


class InverseRelationshipTypeManager(RelationshipTypeManager):
    _cache_prefix = 'inv'

    def get_queryset(self):
        qs = super(InverseRelationshipTypeManager, self).get_queryset()
        return qs.filter(inverse_name__isnull=False)


class InverseRelationshipType(RelationshipType):
    objects = InverseRelationshipTypeManager()

    @property
    def left(self):
        return self.to_type

    @property
    def right(self):
        return self.from_type

    wq_label_template = "{{inverse_name}}"

    class Meta:
        proxy = INSTALLED
        abstract = not INSTALLED


def get_related_types(cls, **kwargs):
    from wq.db.rest.models import ContentType as RestContentType
    ctypes = set()
    for rtype in cls.objects.filter(**kwargs):
        # This is a DjangoContentType, swap for our custom version
        ctype = RestContentType.objects.get_for_id(rtype.right.pk)
        ctypes.add(ctype)
    return ctypes


def get_related_children(contenttype):
    return get_related_types(RelationshipType, from_type=contenttype)


def get_related_parents(contenttype):
    return get_related_types(InverseRelationshipType, to_type=contenttype)
