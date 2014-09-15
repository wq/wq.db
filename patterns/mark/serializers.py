from rest_framework import serializers

from wq.db.patterns.base.serializers import TypedAttachmentSerializer
import swapper
MarkdownType = swapper.load_model('mark', 'MarkdownType')

from django.conf import settings


class MarkdownSerializer(TypedAttachmentSerializer):
    attachment_fields = ['id', 'summary', 'markdown']
    type_model = MarkdownType

    html = serializers.Field()

    def field_to_native(self, obj, field_name):
        if not getattr(self.parent.opts, 'model', None):
            return super(MarkdownSerializer, self).field_to_native(
                obj, field_name
            )
        from .rest import active_markdown
        request = self.context['request']
        if not field_name:
            field_name = self.source
        return [
            self.to_native(md)
            for md in active_markdown(getattr(obj, field_name), request)
        ]
