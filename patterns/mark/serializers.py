from rest_framework import serializers
from wq.db.patterns.base import serializers as base
import swapper
MarkdownType = swapper.load_model(
    'mark', 'MarkdownType', required=False
)


class MarkdownSerializer(base.TypedAttachmentSerializer):
    attachment_fields = ['id', 'summary', 'markdown']
    type_model = MarkdownType
    html = serializers.ReadOnlyField()


class MarkedModelSerializer(base.AttachedModelSerializer):
    markdown = serializers.SerializerMethodField()

    def get_markdown(self, instance):
        from .rest import active_markdown
        from wq.db.rest import app
        request = self.context['request']
        return app.router.serialize(
            active_markdown(instance.markdown, request),
            many=True
        )

    class Meta:
        list_exclude = ('markdown',)
