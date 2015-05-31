from rest_framework import serializers
from wq.db.patterns.base import serializers as base
import swapper
MarkdownType = swapper.load_model(
    'mark', 'MarkdownType', required=False
)
from .models import Markdown


class MarkdownSerializer(base.TypedAttachmentSerializer):
    attachment_fields = ['id', 'summary', 'markdown']
    type_model = MarkdownType
    html = serializers.ReadOnlyField()

    class Meta(base.TypedAttachmentSerializer.Meta):
        model = Markdown
        list_exclude = ('html',)


class MarkedModelSerializer(base.AttachedModelSerializer):
    markdown = MarkdownSerializer.for_depth(1)(many=True)

    def to_representation(self, instance):
        data = super(MarkedModelSerializer, self).to_representation(instance)
        if 'markdown' not in data or 'request' not in self.context:
            return data

        # Only include active markdown in output
        # (FIXME: ideally this filter would happen *before* initial
        #  serialization)
        from .rest import active_markdown
        request = self.context['request']
        active_ids = active_markdown(
            instance.markdown, request
        ).values_list('pk', flat=True)
        data['markdown'] = [
            markdown for markdown in data['markdown']
            if markdown['id'] in active_ids
        ]
        return data

    class Meta:
        list_exclude = ('markdown',)
