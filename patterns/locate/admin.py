from django.contrib.gis import admin
from django.contrib.gis.db import models
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Location, SRID


class LocationInline(GenericTabularInline):
    model = Location
    extra = 1  # Otherwise OpenLayers will not initialize properly...

    # Mimics GeoModelAdmin.formfield_for_dbfield
    # (since there is not an Inline version of GeoModelAdmin)
    def formfield_for_dbfield(self, db_field, **kwargs):
        if isinstance(db_field, models.GeometryField):
            kwargs.pop('request', None)
            # Use parent (LocatedModelAdmin) class to actually get_map_widget
            kwargs['widget'] = self.admin_site._registry.get(
                self.parent_model
            ).get_map_widget(
                db_field
            )
            return db_field.formfield(**kwargs)
        else:
            return super(LocationInline, self).formfield_for_dbfield(
                db_field, **kwargs
            )


class LocatedModelAdmin(admin.GeoModelAdmin):
    inlines = [LocationInline]
    geom_type = 'POINT'
    map_width = 300
    map_height = 200
    map_srid = SRID
    default_zoom = 1
    point_zoom = 10

    # GeoModelAdmin does not know how to handle generic GEOMETRY types;
    # Need to explicitly set geom_type
    def get_map_widget(self, db_field):
        "Overrides db_field geometry type to ensure a meaningful editor"
        class FakeDbField(object):
            geom_type = self.geom_type
            name = db_field.name
        return super(LocatedModelAdmin, self).get_map_widget(FakeDbField())
