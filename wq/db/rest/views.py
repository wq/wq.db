from rest_framework.generics import GenericAPIView as RestGenericAPIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, viewsets
from django.db.models import ProtectedError


class GenericAPIView(RestGenericAPIView):
    router = None
    ignore_kwargs = []

    @property
    def template_name(self):
        """
        Infer template name from view/viewset name
        """
        name = type(self).__name__
        name = name.replace("ViewSet", "")
        name = name.replace("View", "")
        return name.lower() + ".html"

    @property
    def depth(self):
        return 0

    def get_template_names(self):
        return [self.template_name]

    def get_queryset(self):
        if self.router is not None and self.model is not None:
            return self.router.get_queryset_for_model(self.model, self.request)
        return super(GenericAPIView, self).get_queryset()

    def get_serializer_class(self):
        if self.router is not None and self.model is not None:
            return self.router.get_serializer_for_model(self.model, self.depth)
        return super(GenericAPIView, self).get_serializer_class()

    def head(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class SimpleView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        return Response({})


class SimpleViewSet(viewsets.ViewSet, GenericAPIView):
    def list(self, request, *args, **kwargs):
        return Response({})


class ModelViewSet(viewsets.ModelViewSet, GenericAPIView):
    @property
    def template_name(self):
        basename = self.model._meta.model_name
        if self.action in ("retrieve", "create", "update", "delete"):
            suffix = "detail"
        elif self.action and self.action != "metadata":
            suffix = self.action
        else:
            suffix = "list"
        return "%s_%s.html" % (basename, suffix)

    @property
    def depth(self):
        if self.action in ("retrieve", "edit"):
            return 1
        else:
            return 0

    @action(detail=True)
    def edit(self, request, *args, **kwargs):
        """
        Edit view (note: form and lookup context now generated on client)
        """
        return self.retrieve(request, *args, **kwargs)

    def new(self, request):
        """
        new is a variant of the "edit" action, but with no existing model
        to lookup.
        """
        self.action = "edit"
        return Response({})

    def retrieve(self, request, *args, **kwargs):
        """
        Custom retrieve watches for "new" lookup value and switches modes
        accordingly
        """
        lookup = self.lookup_url_kwarg or self.lookup_field

        if self.kwargs.get(lookup, "") == "new":
            # new/edit mode
            return self.new(request)
        else:
            # Normal detail view
            return super(ModelViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        response = super(ModelViewSet, self).list(request, *args, **kwargs)
        if not isinstance(response.data, dict):
            return response

        if not self.router:
            return response

        if len(set(self.kwargs) - {"format"}) == 0:
            return response

        return self.add_parent_info(request, response)

    def create(self, request, *args, **kwargs):
        response = super(ModelViewSet, self).create(request, *args, **kwargs)
        if not request.accepted_media_type.startswith("text/html"):
            # JSON request, assume client will handle redirect
            return response

        # HTML request, probably a form post from an older browser
        if response.status_code == status.HTTP_201_CREATED:
            return self.postsave(request, response)
        else:
            return self.saveerror(request, response)

    def update(self, request, *args, **kwargs):
        response = super(ModelViewSet, self).update(request, *args, **kwargs)
        if not request.accepted_media_type.startswith("text/html"):
            # JSON request, assume client will handle redirect
            return response

        # HTML request, probably a form post from an older browser
        if response.status_code == status.HTTP_200_OK:
            return self.postsave(request, response)
        else:
            return self.saveerror(request, response)

    def postsave(self, request, response):
        if self.router:
            conf = self.router.get_config_for_model(self.model)
        else:
            conf = {}

        # Redirect to new page
        postsave = conf.get(
            "postsave", self.model._meta.model_name + "_detail"
        )
        if "_" in postsave:
            page, mode = postsave.split("_")
        else:
            page = postsave
            mode = "detail"

        oid = ""
        if page != self.model._meta.model_name and self.router:
            # Optional: return to detail view of a parent model
            pconf = self.router.get_page_config(page)
            if pconf.get("list", None) and mode != "list":
                oid = response.data.get(page + "_id", None)
        else:
            # Default: return to detail view of the saved model
            pconf = conf
            if mode != "list":
                oid = response.data["id"]

        url = "/" + pconf["url"]
        if pconf["url"] and pconf.get("list", None):
            url += "/"
        if oid:
            url += str(oid)
            if mode == "edit":
                url += "/edit"

        return Response(
            {"detail": "Created"},
            status=status.HTTP_302_FOUND,
            headers={"Location": url},
        )

    def saveerror(self, request, response):
        errors = [
            {"field": key, "errors": val} for key, val in response.data.items()
        ]
        template = self.model._meta.model_name + "_error.html"
        return Response(
            {"errors": errors, "post": request.DATA},
            status=response.status_code,
            template_name=template,
        )

    def destroy(self, request, *args, **kwargs):
        try:
            response = super(ModelViewSet, self).destroy(
                request, *args, **kwargs
            )
        except ProtectedError as e:
            return Response({"non_field_errors": [e.args[0]]}, status=400)
        else:
            return response

    def add_parent_info(self, request, response):
        parent_model = None
        pid = None
        for rel_model, fields in self.router.get_foreign_keys(
            self.model
        ).items():
            if len(fields) == 1 and fields[0] in self.kwargs:
                pid = self.kwargs[fields[0]]
                parent_model = rel_model

        if not parent_model:
            return response

        parent = self.router.get_by_identifier(
            self.router.get_queryset_for_model(parent_model, request), pid
        )
        objid = self.router.get_object_id(parent)
        page_config = self.router.get_model_config(parent_model)
        urlbase = page_config["url"]
        if urlbase != "":
            urlbase += "/"
        response.data["parent_label"] = str(parent)
        response.data["parent_id"] = objid
        response.data["parent_url"] = "%s%s" % (urlbase, objid)
        response.data["parent_is_" + page_config["name"]] = True
        response.data["parent_page"] = page_config["name"]
        response.data["page_config"] = page_config
        response.data["parent"] = self.router.serialize(
            parent,
            request=self.request,
        )
        return response
