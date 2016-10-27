from wq.db import rest
from .models import FileType


rest.router.register_model(
    FileType,
    fields="__all__",
)
