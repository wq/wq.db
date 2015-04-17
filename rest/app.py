import warnings
warnings.warn(
    "The wq.db.rest.app API has been moved to wq.db.rest. "
    "The actual Router implementation has moved to wq.db.rest.routers",
    DeprecationWarning
)


from . import ModelRouter as Router, router, autodiscover  # NOQA
