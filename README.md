[![wq.db](https://raw.github.com/wq/wq/master/images/256/wq.db.png)](https://wq.io/wq.db)

[wq.db](https://wq.io/wq.db) is a collection of Python modules for building robust, flexible schemas and REST APIs for use in creating field data collection apps and (more generally) mobile-first websites with progressive enhancement.  wq.db is the backend component of [wq] and is geared primarily for use with [wq.app], though it can be used separately.  wq.db is built on the [Django] platform.


[![Latest PyPI Release](https://img.shields.io/pypi/v/wq.db.svg)](https://pypi.org/project/wq.db)
[![Release Notes](https://img.shields.io/github/release/wq/wq.db.svg)](https://github.com/wq/wq.db/releases)
[![Documentation](https://img.shields.io/badge/Docs-1.1-blue.svg)](https://wq.io/wq.db)
[![License](https://img.shields.io/pypi/l/wq.db.svg)](https://wq.io/license)
[![GitHub Stars](https://img.shields.io/github/stars/wq/wq.db.svg)](https://github.com/wq/wq.db/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/wq/wq.db.svg)](https://github.com/wq/wq.db/network)
[![GitHub Issues](https://img.shields.io/github/issues/wq/wq.db.svg)](https://github.com/wq/wq.db/issues)

[![Travis Build Status](https://img.shields.io/travis/wq/wq.db/master.svg)](https://travis-ci.org/wq/wq.db)
[![Python Support](https://img.shields.io/pypi/pyversions/wq.db.svg)](https://pypi.org/project/wq.db)
[![Django Support](https://img.shields.io/pypi/djversions/wq.db.svg)](https://pypi.org/project/wq.db)

#### Support Matrix

wq.db 1.1 is compatible with Django 1.11 and newer, and optimized for Python 3.

&nbsp;      | Python | Django | Django REST Framework
------------|--------|--------|-----------------------
**wq.db 1.0** | 2.7, 3.4, 3.5, 3.6 | 1.8, 1.10, 1.11 | 3.6
**wq.db 1.1** | 2.7?*, 3.4, 3.5, 3.6, 3.7 | 1.11, 2.0, 2.1 | 3.9
**wq.db 2.0 (Future)** | 3.4+ | 2.0+ | TBD

&#42; Python 2.7 support is no longer tested, though it might still work for now.

## Getting Started

```bash

# Recommended: create virtual environment
# python3 -m venv venv
# . venv/bin/activate

# Install entire wq suite (recommended)
pip install wq

# Install only wq.db
pip install wq.db
```

See [the documentation] for more information.

## Features

wq.db provides the following modules:

### [wq.db.rest]
Extends the excellent [Django REST Framework] with a collection of views, serializers, and context processors useful for creating a progresively enhanced website that serves as its own mobile app and [its own REST API].  The core of the library is an admin-like [ModelRouter] that connects REST urls to registered models, and provides a descriptive [configuration object] for consumption by [wq.app's client-side router].  wq.db.rest also includes a GeoJSON serializer/renderer.

### [wq.db.patterns]
A collection of abstract models and serializers for use in constructing advanced [design patterns] including [nested forms], [EAV structures][EAV], and [natural keys].  Includes [wq.db.patterns.identify][identify], an installable Django app module to help manage third-party entity identifers.

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
[design patterns]: https://wq.io/docs/about-patterns
[nested forms]: https://wq.io/docs/nested-forms
[EAV]: https://wq.io/docs/eav-vs-relational
[natural keys]: https://github.com/wq/django-natural-keys
