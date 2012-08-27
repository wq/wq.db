from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class RelatedModel(models.Model):
    relationships = generic.GenericRelation('Relationship',
        content_type_field='from_content_type',
        object_id_field='from_object_id',
        related_name='%(class)s_set'
    )
    inverse_relationships = generic.GenericRelation('InverseRelationship',
        content_type_field='to_content_type',
        object_id_field='to_object_id',
        related_name='%(class)s_inverse_set'
    )

    def all_relationships(self):
        for rel in self.relationships.all():
            yield rel
        for rel in self.inverse_relationships.all():
            yield rel

    class Meta:
        abstract = True

class Relationship(models.Model):

    type                = models.ForeignKey('RelationshipType')

    # Objects can contain pointers to any model
    from_content_type   = models.ForeignKey(ContentType, related_name='+')
    from_object_id      = models.PositiveIntegerField()
    from_content_object = generic.GenericForeignKey('from_content_type', 'from_object_id')
    
    to_content_type     = models.ForeignKey(ContentType, related_name='+')
    to_object_id        = models.PositiveIntegerField()
    to_content_object   = generic.GenericForeignKey('to_content_type', 'to_object_id')
    
    @property
    def left(self):
        return self.from_content_object
   
    @property
    def right(self):
        return self.to_content_object

    @right.setter
    def right(self, value):
        self.to_content_object = value

    def right_object_id(self):
        return self.to_object_id

    @property
    def reltype(self):
        return self.type

    def save(self, *args, **kwargs):
        rightct = self.reltype.right
        self.right = rightct.get_object_for_this_type(pk = self.right_object_id)
        super(Relationship, self).save(*args, **kwargs)
    
    def __unicode__(self):
        if self.from_content_type_id and self.type_id and self.to_content_type_id:
            return '%s %s %s' % (self.left, self.reltype, self.right)
	else:
	    return 'Undefined'

    class Meta:
        db_table = 'wq_relationship'

class InverseRelationship(Relationship):
    @property
    def left(self):
        return self.to_content_object

    @property
    def right(self):
        return self.from_content_object
    
    @right.setter
    def right(self, value):
        self.from_content_object = value

    def right_object_id(self):
        return self.from_object_id

    @property
    def reltype(self):
        return InverseRelationshipType.objects.filter(pk=self.type.pk)[0]
    
    class Meta:
        proxy = True

class RelationshipType(models.Model):
    name           = models.CharField(max_length=255)
    inverse_name   = models.CharField(max_length=255)
#   implicit       = models.BooleanField()

    from_type      = models.ForeignKey(ContentType, related_name='+')
    to_type        = models.ForeignKey(ContentType, related_name='+')
    
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

class InverseRelationshipType(RelationshipType):
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
