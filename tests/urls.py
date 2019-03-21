from django.urls import include, path
from wq.db import rest
from tests.patterns_app.views import FilterableView


urlpatterns = [
    path('filterable/<path:ids>', FilterableView.as_view()),
    path('', include(rest.router.urls)),
]
