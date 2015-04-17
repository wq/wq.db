from wq.db import rest
from .models import Markdown
from .serializers import MarkdownSerializer

import swapper
MarkdownType = swapper.load_model("mark", "MarkdownType")


def active_markdown(qs, request):
    mtype = MarkdownType.get_current(request)
    return qs.filter(type=mtype)

rest.router.register_model(
    Markdown,
    serializer=MarkdownSerializer,
    filter=active_markdown,
    url='markdown',
)
rest.router.register_model(MarkdownType)
