from django.contrib.contenttypes import generic
from django.contrib import admin
from django import forms

from wq.relate.models import Relationship, InverseRelationship, RelationshipType, InverseRelationshipType, RelatedModel

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
    model = RelatedModel
    inlines = [
      RelationshipInline,
      InverseRelationshipInline
    ]
