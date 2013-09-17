from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from wq.db.patterns.base import SerializableGenericRelation


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
            if kwargs.get('inverse', False):
                data = data.filter(relationships__to_content_type=ctype,
                                   relationships__to_object_id__in=
                                   [obj.pk for obj in objs])
            else:
                data = data.filter(
                    inverserelationships__from_content_type=ctype,
                    inverserelationships__from_object_id__in=
                    [obj.pk for obj in objs]
                )
        return data


class RelatedModel(models.Model):
    relationships = SerializableGenericRelation(
        'Relationship',
        content_type_field='from_content_type',
        object_id_field='from_object_id',
        related_name='%(class)s_set'
    )
    inverserelationships = SerializableGenericRelation(
        'InverseRelationship',
        content_type_field='to_content_type',
        object_id_field='to_object_id',
        related_name='%(class)s_inverse_set'
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
    from_content_object = generic.GenericForeignKey(
        'from_content_type', 'from_object_id'
    )

    to_content_type = models.ForeignKey(ContentType, related_name='+')
    to_object_id = models.PositiveIntegerField()
    to_content_object = generic.GenericForeignKey(
        'to_content_type', 'to_object_id'
    )

    computed = models.BooleanField(default=False)

    objects = RelationshipManager()

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
    def reltype(self):
        return self.type

    def save(self, *args, **kwargs):
        rightct = self.reltype.right
        self.right = rightct.get_object_for_this_type(pk=self.right_object_id)
        super(Relationship, self).save(*args, **kwargs)

    def __unicode__(self):
        if (self.from_content_type_id and self.type_id
                and self.to_content_type_id):
            return u'%s %s %s' % (self.left, self.reltype, self.right)
        else:
            return 'Undefined'

    class Meta:
        db_table = 'wq_relationship'


class InverseRelationshipManager(models.Manager):
    def get_query_set(self):
        qs = super(InverseRelationshipManager, self).get_query_set()
        return qs.filter(type__inverse_name__isnull=False)


class InverseRelationship(Relationship):
    objects = InverseRelationshipManager()

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
    def reltype(self):
        return InverseRelationshipType.objects.get(pk=self.type.pk)

    class Meta:
        proxy = True


class RelationshipType(models.Model):
    name = models.CharField(max_length=255)
    inverse_name = models.CharField(max_length=255, null=True, blank=True)

    from_type = models.ForeignKey(ContentType, related_name='+')
    to_type = models.ForeignKey(ContentType, related_name='+')

    computed = models.BooleanField(default=False)

    @property
    def left(self):
        return self.from_type

    @property
    def right(self):
        return self.to_type

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'wq_relationshiptype'


class InverseRelationshipTypeManager(models.Manager):
    def get_query_set(self):
        qs = super(InverseRelationshipTypeManager, self).get_query_set()
        return qs.filter(inverse_name__isnull=False)


class InverseRelationshipType(RelationshipType):
    objects = InverseRelationshipTypeManager()

    @property
    def left(self):
        return self.to_type

    @property
    def right(self):
        return self.from_type

    def __unicode__(self):
        return self.inverse_name

    class Meta:
        proxy = True
