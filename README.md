[![wq.db](https://raw.github.com/wq/wq/master/images/256/wq.db.png)](http://wq.io/wq.db)
  
**[wq.db]** is a collection of Python modules for building robust, flexible schemas and REST APIs for use in field data collection apps and (more generally) progressively enhanced mobile-first websites.  wq.db is the backend component of [wq] and is geared primarily for use with [wq.app], though it can be used separately.  wq.db is built on the [Django] platform.

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
Extends the excellent [Django Rest Framework](http://django-rest-framework.org) with a collection of views, serializers, and context processors useful for creating a progresively enhanced website that serves as its own mobile app and its own REST API.  The core of the library (app.py) includes an admin-style `autodiscover()` that automatically routes REST urls to installed models, and provides a descriptive JSON configuration object for consumption by [wq.app's client-side router].  wq.db.rest also includes a CRS-aware GeoJSON serializer and renderer.

### [wq.db.patterns]
A collection of recommended design patterns ([annotate], [identify], [locate], and [relate]) that provide long-term flexibility and sustainability for data collection systems.  These patterns are implemented as installable Django apps.

### Batteries Included
Like Django itself, wq.db includes a `contrib` module that provides additional functionality not considered to be part of the "core" library.

#### [files]
Generic file manager.  Supports using the same `FileField` for both images and files.  Also includes a URL-driven thumbnail generator.

#### [vera]
Reference implementation of the ERAV model, an extention to EAV with support for maintaining multiple versions of an entity.

[wq]: http://wq.io
[wq.db]: http://wq.io/wq.db
[Django]: https://www.djangoproject.com/
[the documentation]: http://wq.io/docs/
[wq.db.rest]: http://wq.io/docs/rest
[wq.app]: http://wq.io/wq.app
[wq.app's client-side router]: http://wq.io/docs/app-js
[wq.db.patterns]: http://wq.io/docs/about-patterns
[wq.db.contrib]: #wqdbcontrib
[annotate]: http://wq.io/docs/annotate
[identify]: http://wq.io/docs/identify
[locate]: http://wq.io/docs/locate
[relate]: http://wq.io/docs/relate
[files]: http://wq.io/docs/files
[vera]: http://wq.io/vera
