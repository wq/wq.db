[![wq.db](https://raw.github.com/wq/wq/master/images/256/wq.db.png)](http://wq.io/wq.db)
  
[wq.db](http://wq.io/wq.db) is a collection of Python modules for building robust, flexible schemas and REST APIs for use in creating field data collection apps and (more generally) mobile-first websites with progressive enhancement.  wq.db is the backend component of [wq] and is geared primarily for use with [wq.app], though it can be used separately.  wq.db is built on the [Django] platform.

[![Build Status](https://travis-ci.org/wq/wq.db.png?branch=master)](https://travis-ci.org/wq/wq.db)
[![PyPI Package](https://pypip.in/version/wq.db/badge.png)](https://pypi.python.org/pypi/wq.db)

Tested on Python 2.7 and 3.4, with Django 1.6 and 1.7.

## Getting Started

```bash
pip install wq.db
# Or, if using together with wq.app and/or wq.io
pip install wq
```

See [the documentation] for more information.

## Features

wq.db provides following modules:

### [wq.db.rest]
Extends the excellent [Django REST Framework] with a collection of views, serializers, and context processors useful for creating a progresively enhanced website that serves as its own mobile app and [its own REST API].  The core of the library ([app.py]) includes an admin-style Router that connects REST urls to registered models, and provides a descriptive [configuration object] for consumption by [wq.app's client-side router].  wq.db.rest also includes a CRS-aware GeoJSON serializer/renderer.

### [wq.db.patterns]
A collection of [design patterns] (e.g. [identify], [relate]) that provide long-term flexibility and sustainability for user-maintained data collection applications.  These patterns are implemented as installable Django apps.

### [wq.db.contrib]
Like Django itself, wq.db includes a [contrib] module that provides additional functionality not considered to be part of the "core" library, including a [file manager], a [search] API, and a [chart] backend.

[wq]: http://wq.io
[Django]: https://www.djangoproject.com/
[the documentation]: http://wq.io/docs/
[wq.db.rest]: http://wq.io/docs/about-rest
[wq.app]: http://wq.io/wq.app
[its own REST API]: http://wq.io/docs/website-rest-api
[wq.app's client-side router]: http://wq.io/docs/app-js
[Django REST Framework]: http://django-rest-framework.org
[app.py]: http://wq.io/docs/app.py
[configuration object]: http://wq.io/docs/config
[wq.db.patterns]: http://wq.io/docs/about-patterns
[design patterns]: http://wq.io/docs/about-patterns
[identify]: http://wq.io/docs/identify
[relate]: http://wq.io/docs/relate
[wq.db.contrib]: http://wq.io/chapters/contrib/docs
[contrib]: http://wq.io/chapters/contrib/docs
[file manager]: http://wq.io/docs/files
[search]: http://wq.io/docs/search
[chart]: http://wq.io/docs/chart
