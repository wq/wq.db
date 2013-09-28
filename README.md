[<img src="https://raw.github.com/wq/wq/master/images/512/wq.db.png"
  width="256" height="256"
  alt="wq.db">]
  (http://wq.io/wq.db)
  
**[wq.db]** is a collection of Django modules for building robust, flexible schemas and REST APIs for use in field data collection apps and (more generally) progressively enhanced mobile-first websites.  wq.db is a submodule of [wq] and contains three sub-submodules:
* **[wq.db.rest]**: Django Rest Framework extensions for creating self-describing REST APIs with built-in support for progressive enhancement
* **[wq.db.patterns]**: Django models and ORM utilities for robust design patterns
* **[wq.db.contrib]**: Additional modules for common use cases

## wq.db.rest
Extends the excellent [Django Rest Framework](http://django-rest-framework.org) with a collection of views, serializers, and context processors useful for creating a progresively enhanced website that serves as its own mobile app and its own REST API.  The core of the library (app.py) includes an admin-style `autodiscover()` that automatically routes REST urls to installed models, and provides a descriptive JSON configuration object for consumption by [wq.app's client-side router].  wq.db.rest also includes a CRS-aware GeoJSON serializer and renderer.

### Example Usage

```python
# urls.py
from wq.db.rest import app
app.autodiscover()
app.router.add_page('index', {'map': True})

urlpatterns = patterns('',
    url(r'^', include(app.router.urls))
# ...
```

## [wq.db.patterns]

A collection of recommended design patterns (`annotate`, `identify`, `locate`, and `relate`) for data collection systems, implemented as installable Django apps.

### Example Usage

```python
# settings.py
INSTALLED_APPS = (
   # ...
   'wq.db.patterns.annotate'
)

# myapp/models.py
from wq.db.patterns import models
class Report(models.AnnotatedModel):
   date = models.DateField()
   # ...
```

### [annotate] Pattern
Generic entity-attribute-value (EAV) implementation.  Particularly useful for building field data collection apps where the parameters being collected may change over time (i.e. nearly all data collection apps).  To add new parameter definitions, a project administrator can use a web interface (add rows), instead of needing to have a developer change the database schema (add columns).  The [Vera module] extends `annotate` with support for tracking multiple versions of data.

### [identify] Pattern
Helps manage entities with multiple unique identifiers, for example water quality monitoring sites which may have one or more project-specific, state, and/or federal identifying codes.  Extends Django's built in model `Manager` with a `get_by_identifier()` method.

### [locate] Pattern
Helps manage geographic data for entities that may have more than one geometry (for example a city may be represented as both a point and a polygon).

### [relate] Pattern
Generic implementation of typed many-to-many relationships.  Eliminates the need to create dozens of linking tables in the database.  Extends Django's built in model `Manager` with a `filter_by_related()` method.

## wq.db.contrib
Contains useful additions to wq.db that are not considered part of the "core" library.

### [files]
Generic file manager.  Supports using the same `FileField` for both images and files.  Also includes a URL-driven thumbnail generator.

### [vera]
Reference implementation of the ERAV model, an extention to EAV with support for maintaining multiple versions of an entity.

[wq]: http://wq.io
[wq.db]: http://wq.io/wq.db
[wq.db.rest]: http://wq.io/docs/rest
[wq.app's client-side router]: http://wq.io/docs/app.js
[wq.db.patterns]: http://wq.io/docs/about-patterns
[Vera module]: http://wq.io/vera
[wq.db.contrib]: #wqdbcontrib
[annotate]: http://wq.io/docs/annotate
[identify]: http://wq.io/docs/identify
[locate]: http://wq.io/docs/locate
[relate]: http://wq.io/docs/relate
[files]: http://wq.io/docs/files
[vera]: http://wq.io/vera
