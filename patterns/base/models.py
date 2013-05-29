from django.db import models

class NaturalKeyModelManager(models.Manager):
    """
    Manager for use with subclasses of NaturalKeyModel.
    """

    def get_by_natural_key(self, *args):
        """
        Return the object corresponding to the provided natural key.

        (This is a generic implementation of the standard Django function)
        """

        kwargs = self.natural_key_kwargs(*args)

        # Since kwargs already has __ lookups in it, we could just do this:
        # return self.get(**kwargs)

        # But, we should call each related model's get_by_natural_key in case 
        # it's been overridden
        for name, rel_to in self.model.get_natural_key_info():
            if rel_to:
                # Extract natural key for related object
                nested_key = rel_to.get_natural_key_fields()
                nargs = [
                    kwargs.pop(name + '__' + nname)
                    for nname in nested_key
                ]

                # Update kwargs with related object
                try:
                    kwargs[name] = rel_to.objects.get_by_natural_key(*nargs)
                except rel_to.DoesNotExist:
                    # If related object doesn't exist, assume this one doesn't either
                    raise self.model.DoesNotExist()

        return self.get(**kwargs)

    def create_by_natural_key(self, *args):
        """
        Create a new object from the provided natural key values.  If the
        natural key contains related objects, recursively get or create them by
        their natural keys.
        """

        kwargs = self.natural_key_kwargs(*args) 
        for name, rel_to in self.model.get_natural_key_info():
            # Automatically create any related objects as needed
            if rel_to:
                nested_key = rel_to.get_natural_key_fields()
                nargs = []
                for nname in nested_key:
                    nargs.append(kwargs.pop(name + '__' + nname))
                kwargs[name], is_new = rel_to.objects.get_or_create_by_natural_key(*nargs)
        return self.create(**kwargs)

    def get_or_create_by_natural_key(self, *args):
        """
        get_or_create + get_by_natural_key
        """
        try:
            return self.get_by_natural_key(*args), False
        except self.model.DoesNotExist:
            return self.create_by_natural_key(*args), True

    # Shortcut for common use case
    def find(self, *args):
        """
        Shortcut for get_or_create_by_natural_key that discards the "created"
        boolean.
        """
        obj, is_new = self.get_or_create_by_natural_key(*args)
        return obj

    def natural_key_kwargs(self, *args):
        """
        Convert args into kwargs by merging with model's natural key field names
        """
        natural_key = self.model.get_natural_key_fields()
        if len(args) != len(natural_key):
            raise TypeError("Wrong number of values, expected %s"
                            % len(natural_key))
        return dict(zip(natural_key, args))

        
class NaturalKeyModel(models.Model):
    """
    Abstract class with a generic implementation of natural_key.
    """

    objects = NaturalKeyModelManager()

    @classmethod
    def get_natural_key_info(cls):
        """
        Derive natural key from first unique_together definition, noting which
        fields are related objects vs. regular fields.
        """
        fields = cls._meta.unique_together[0]
        info = []
        for name in fields:
            field = cls._meta.get_field_by_name(name)[0]
            rel_to = field.rel.to if field.rel else None
            info.append((name, rel_to))
        return info

    @classmethod
    def get_natural_key_fields(cls):
        """
        Determine actual natural key field list, incorporating the natural keys
        of related objects as needed.
        """
        natural_key = []
        for name, rel_to in cls.get_natural_key_info():
            if not rel_to:
                natural_key.append(name)
            else:
                nested_key = rel_to.get_natural_key_fields()
                natural_key.extend([
                    name + '__' + nname
                    for nname in nested_key
                ])
        return natural_key
        

    def natural_key(self):
        """
        Return the natural key for this object.

        (This is a generic implementation of the standard Django function)
        """
        # Recursively extract properties from related objects if needed
        vals = [reduce(getattr, name.split('__'), self)
                for name in self.get_natural_key_fields()]
        return vals

    class Meta:
        abstract = True
