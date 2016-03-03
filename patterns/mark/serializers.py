from rest_framework import serializers
from wq.db.patterns.base import serializers as base
import swapper

from .models import Markdown
MarkdownType = swapper.load_model(
    'mark', 'MarkdownType', required=False
)


def active_markdown(qs, request):
    mtype = MarkdownType.get_current(request)
    return qs.filter(type=mtype)


class MarkdownSerializer(base.TypedAttachmentSerializer):
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
        request = self.context['request']
        active_ids = active_markdown(
            instance.markdown, request
        ).values_list('pk', flat=True)
        data['markdown'] = [
            markdown for markdown in data['markdown']
            if markdown['id'] in active_ids
        ]
        return data
