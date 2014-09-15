from wq.db.rest import app
from .models import Markdown
from .serializers import MarkdownSerializer

import swapper
MarkdownType = swapper.load_model("mark", "MarkdownType")


def active_markdown(qs, request):
    mtype = MarkdownType.get_current(request)
    return qs.filter(type=mtype)

app.router.register_model(
    Markdown,
    serializer=MarkdownSerializer,
    filter=active_markdown,
    url='markdown',
)
app.router.register_model(MarkdownType)
