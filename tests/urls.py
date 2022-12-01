from django.urls import path
from wq.db import rest
from .settings import WITH_NONROOT


if WITH_NONROOT:
    base_url = "wqsite/"
else:
    base_url = ""


urlpatterns = [
    path(base_url, rest.router.urls),
]
