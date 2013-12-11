[![wq.db](https://raw.github.com/wq/wq/master/images/256/wq.db.png)](http://wq.io/wq.db)
  
[wq.db] is a collection of Python modules for building robust, flexible schemas and REST APIs for use in creating field data collection apps and (more generally) mobile-first websites with progressive enhancement.  wq.db is the backend component of [wq] and is geared primarily for use with [wq.app], though it can be used separately.  wq.db is built on the [Django] platform.

[![Build Status](https://travis-ci.org/wq/wq.db.png?branch=master)](https://travis-ci.org/wq/wq.db)

## Getting Started

```bash
pip install wq.db
# Or, if using together with wq.app and/or wq.io
pip install wq
```

See [the documentation] for more information.

## Features

wq.db has two primary components: a REST API generator ([wq.db.rest]) and a collection of schema design patterns ([wq.db.patterns]) that facilitate flexible database layouts.

### [wq.db.rest]
Extends the excellent [Django REST Framework] with a collection of views, serializers, and context processors useful for creating a progresively enhanced website that serves as its own mobile app and [its own REST API].  The core of the library ([app.py]) includes an admin-style Router that connects REST urls to registered models, and provides a descriptive [configuration object] for consumption by [wq.app's client-side router].  wq.db.rest also includes a CRS-aware GeoJSON serializer/renderer.

### [wq.db.patterns]
A collection of recommended design patterns ([annotate], [identify], [locate], and [relate]) that provide long-term flexibility and sustainability for user-maintained data collection applications.  These patterns are implemented as installable Django apps.

### Batteries Included
Like Django itself, wq.db includes a [contrib] module that provides additional functionality not considered to be part of the "core" library.

#### [dbio]
Load data from external files into the database, powered by [wq.io], [files], and [vera].

#### [files]
Generic file manager.  Supports using the same `FileField` for both images and files.  Also includes a URL-driven thumbnail generator.

#### [search]
Views for searching and disambiguating models using the [identify] and [annotate] patterns.

#### [vera]
Reference implementation of the [ERAV] model, an extension to EAV with support for maintaining multiple versions of an entity.

[wq]: http://wq.io
[wq.db]: http://wq.io/wq.db
[Django]: https://www.djangoproject.com/
[the documentation]: http://wq.io/docs/
[wq.db.rest]: http://wq.io/docs/about-rest
[wq.app]: http://wq.io/wq.app
[its own REST API]: http://wq.io/docs/website-rest-api
[wq.app's client-side router]: http://wq.io/docs/app-js
[wq.db.patterns]: http://wq.io/docs/about-patterns
[Django REST Framework]: http://django-rest-framework.org
[app.py]: http://wq.io/docs/app.py
[configuration object]: http://wq.io/docs/config
[annotate]: http://wq.io/docs/annotate
[identify]: http://wq.io/docs/identify
[locate]: http://wq.io/docs/locate
[relate]: http://wq.io/docs/relate
[contrib]: http://wq.io/docs/?section=contrib
[dbio]: http://wq.io/docs/dbio
[wq.io]: http://wq.io/wq.io
[search]: http://wq.io/docs/search
[files]: http://wq.io/docs/files
[vera]: http://wq.io/vera
[ERAV]: http://wq.io/research/provenance
