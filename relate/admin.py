from django.contrib.contenttypes import generic
from django.contrib import admin
from django import forms

from wq.db.relate.models import Relationship, InverseRelationship, RelationshipType, InverseRelationshipType, RelatedModel

class InverseRelationshipForm(forms.ModelForm):
    type = forms.models.ModelChoiceField(queryset=InverseRelationshipType.objects.all())

class RelationshipInline(generic.GenericTabularInline):
    model = Relationship
    ct_field = "from_content_type"
    ct_fk_field = "from_object_id"
    extra = 0
    readonly_fields = ('to_content_object',)

class InverseRelationshipInline(generic.GenericTabularInline):
    model = InverseRelationship
    ct_field = "to_content_type"
    ct_fk_field = "to_object_id"
    form = InverseRelationshipForm
    extra = 0
    readonly_fields = ('from_content_object',)

class RelatedModelAdmin(admin.ModelAdmin):
    model = RelatedModel
    inlines = [
      RelationshipInline,
      InverseRelationshipInline
    ]
