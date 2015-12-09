[![wq.db](https://raw.github.com/wq/wq/master/images/256/wq.db.png)](https://wq.io/wq.db)

[wq.db](https://wq.io/wq.db) is a collection of Python modules for building robust, flexible schemas and REST APIs for use in creating field data collection apps and (more generally) mobile-first websites with progressive enhancement.  wq.db is the backend component of [wq] and is geared primarily for use with [wq.app], though it can be used separately.  wq.db is built on the [Django] platform.


[![Latest PyPI Release](https://img.shields.io/pypi/v/wq.db.svg)](https://pypi.python.org/pypi/wq.db)
[![Release Notes](https://img.shields.io/github/release/wq/wq.db.svg)](https://github.com/wq/wq.db/releases)
[![Documentation](https://img.shields.io/badge/Docs-0.8-blue.svg)](https://wq.io/wq.db)
[![License](https://img.shields.io/pypi/l/wq.db.svg)](https://wq.io/license)
[![GitHub Stars](https://img.shields.io/github/stars/wq/wq.db.svg)](https://github.com/wq/wq.db/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/wq/wq.db.svg)](https://github.com/wq/wq.db/network)
[![GitHub Issues](https://img.shields.io/github/issues/wq/wq.db.svg)](https://github.com/wq/wq.db/issues)

[![Travis Build Status](https://img.shields.io/travis/wq/wq.db/master.svg)](https://travis-ci.org/wq/wq.db)
[![Python Support](https://img.shields.io/pypi/pyversions/wq.db.svg)](https://pypi.python.org/pypi/wq.db)
[![Django Support](https://img.shields.io/badge/Django-1.7%2C%201.8-blue.svg)](https://pypi.python.org/pypi/wq.db)

#### Support Matrix

The latest version of wq.db is only compatible with Django REST Framework 3.  The following library versions are supported:

&nbsp;      | Python | Django | Django REST Framework
------------|--------|--------|-----------------------
**wq.db 0.8.3** | 2.7 & 3.4 | 1.7 & 1.8 | 3.3
**wq.db 0.7.2** | 2.7 & 3.4 | 1.6 & 1.7 | 2.4

## Getting Started

```bash
pip3 install wq.db
# Or, if using together with wq.app and/or wq.io
pip3 install wq
```

See [the documentation] for more information.

## Features

wq.db provides the following modules:

### [wq.db.rest]
Extends the excellent [Django REST Framework] with a collection of views, serializers, and context processors useful for creating a progresively enhanced website that serves as its own mobile app and [its own REST API].  The core of the library is an admin-like [ModelRouter] that connects REST urls to registered models, and provides a descriptive [configuration object] for consumption by [wq.app's client-side router].  wq.db.rest also includes a CRS-aware GeoJSON serializer/renderer.

### [wq.db.patterns]
A collection of [design patterns]&nbsp;(e.g. [identify], [relate]) that provide long-term flexibility and sustainability for user-maintained data collection applications.  These patterns are implemented as installable Django apps.

### [wq.db.contrib]
Like Django itself, wq.db includes a [contrib] module that provides additional functionality not considered to be part of the "core" library, including a [file manager], a [search] API, and a [chart] backend.

[wq]: https://wq.io
[Django]: https://www.djangoproject.com/
[the documentation]: https://wq.io/docs/
[wq.db.rest]: https://wq.io/docs/about-rest
[wq.app]: https://wq.io/wq.app
[its own REST API]: https://wq.io/docs/website-rest-api
[wq.app's client-side router]: https://wq.io/docs/app-js
[Django REST Framework]: http://django-rest-framework.org
[ModelRouter]: https://wq.io/docs/router
[configuration object]: https://wq.io/docs/config
[wq.db.patterns]: https://wq.io/docs/about-patterns
[design patterns]: https://wq.io/docs/about-patterns
[identify]: https://wq.io/docs/identify
[relate]: https://wq.io/docs/relate
[wq.db.contrib]: https://wq.io/chapters/contrib/docs
[contrib]: https://wq.io/chapters/contrib/docs
[file manager]: https://wq.io/docs/files
[search]: https://wq.io/docs/search
[chart]: https://wq.io/docs/chart
