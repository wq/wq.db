from wq.db import rest
import swapper
MarkdownType = swapper.load_model("mark", "MarkdownType")


rest.router.register_model(
    MarkdownType,
    fields="__all__",
)
