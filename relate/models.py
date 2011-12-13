from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib import admin
from django import forms

class RelatedModel(models.Model):
    relations = generic.GenericRelation('Relationship',
      content_type_field='from_content_type',
      object_id_field='from_object_id'
    )
    class Meta:
        abstract = True

class Relationship(models.Model):

    type                = models.ForeignKey('RelationshipType')

    # Objects can contain pointers to any model
    from_content_type   = models.ForeignKey(ContentType, related_name='+', editable = False)
    from_object_id      = models.PositiveIntegerField()
    from_content_object = generic.GenericForeignKey('from_content_type', 'from_object_id')
    
    to_content_type     = models.ForeignKey(ContentType, related_name='+', editable = False)
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
    
    class Meta():
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

class InverseRelationshipType(RelationshipType):
    @property
    def left(self):
       return self.to_type
    
    @property
    def right(self):
       return self.from_type
    
    def __unicode__(self):
        return self.inverse_name

    class Meta():
        proxy = True

# Admin interface
class RelChoicesIter(object):
    def __init__(self, cls):
        rtypes = cls.objects.all()
        self.types = []
        for t in rtypes:
 	    self.types.append(t.right.model_class())

    def __iter__(self):
        for type in self.types:
            for obj in type.objects.all():
                yield (obj.id, str(type) + ': ' + str(obj))

class RelationshipForm(forms.ModelForm):
    to_object_id = forms.ChoiceField(label='Object')
    def __init__(self, **kwargs):
        super(RelationshipForm, self).__init__(**kwargs)
        self.fields['to_object_id'].choices = RelChoicesIter(RelationshipType)

class InverseRelationshipForm(forms.ModelForm):
    type = forms.models.ModelChoiceField(queryset=InverseRelationshipType.objects.all())
    from_object_id = forms.ChoiceField(label='Object')
    def __init__(self, **kwargs):
        super(InverseRelationshipForm, self).__init__(**kwargs)
        self.fields['from_object_id'].choices = RelChoicesIter(InverseRelationshipType)

class RelationshipInline(generic.GenericTabularInline):
    model = Relationship
    ct_field = "from_content_type"
    ct_fk_field = "from_object_id"
    form = RelationshipForm
    extra = 0

class InverseRelationshipInline(generic.GenericTabularInline):
    model = InverseRelationship
    ct_field = "to_content_type"
    ct_fk_field = "to_object_id"
    form = InverseRelationshipForm
    extra = 0

class RelatedModelAdmin(admin.ModelAdmin):
    inlines = [
      RelationshipInline,
      InverseRelationshipInline
    ]

admin.site.register(RelationshipType)
