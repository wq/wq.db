from rest_framework.filters import DjangoFilterBackend
RESERVED_PARAMETERS = ('_', 'page', 'limit', 'format')

#FIXME

class FilterBackend(DjangoFilterBackend):
    def get_query_kwargs_FIXME(self, *args, **kwargs):
        for key, val in self.request.GET.items():
            if key in RESERVED_PARAMETERS:
                continue
            kwargs[key] = val if isinstance(val, unicode) else val[0]

        ctype = get_ct(self.model)
        for key, val in kwargs.items():
            if key in ('target',):
                del kwargs[key]
                continue
            found = False
            for f in self.model._meta.fields:
                if f.name != key and ctype.identifier + f.name != key:
                    continue
                found = True
                if getattr(f, 'rel', None):
                    del kwargs[key]
                    if get_ct(f.rel.to).is_identified:
                        kwargs[f.name] = f.rel.to.objects.get_by_identifier(val)
                    else:
                        kwargs[f.name] = f.rel.to.objects.get(pk=val)
                    self.parent = kwargs[f.name]

            if not found and ctype.is_related:
                for pct in ctype.get_all_parents():
                    if pct.identifier == key:
                        pclass = pct.model_class()
                        if pct.is_identified:
                            self.parent = pclass.objects.get_by_identifier(kwargs[key])
                        else:
                            self.parent = pclass.objects.get(pk=kwargs[key])
                        del kwargs[key]
                        objs = self.model.objects.filter_by_related(self.parent)
                        kwargs['pk__in'] = objs.values_list('pk', flat=True)
                
        kwargs = super(ListOrCreateModelView, self).get_query_kwargs(*args, **kwargs)
        return kwargs
