# -*- coding: utf-8 -*-

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from tests.patterns_app.models import MarkedModel
from wq.db.patterns.models import MarkdownType, Markdown


class MarkTestCase(APITestCase):
    def setUp(self):
        self.en = MarkdownType.objects.create(name="en")
        self.ko = MarkdownType.objects.create(name="ko")
        self.other = MarkdownType.objects.create(name="other")

        self.instance = MarkedModel.objects.create(name="Test")
        self.instance.markdown.create(
            type=self.en,
            summary="Test",
            markdown="**Test**",
        )
        self.instance.markdown.create(
            type=self.ko,
            summary="test",
            markdown="**테스트**",
        )

    def test_mark_simple(self):
        self.assertEqual(
            self.instance.get_html(self.en),
            "<p><strong>Test</strong></p>"
        )
        self.assertEqual(
            self.instance.get_html(self.ko),
            "<p><strong>테스트</strong></p>"
        )

        # Non existing defaults to first markdown item
        self.assertEqual(
            self.instance.get_html(self.other),
            "<p><strong>Test</strong></p>"
        )

    def test_mark_rest_en(self):
        self.rest("en", "<p><strong>Test</strong></p>")

    def test_mark_rest_ko(self):
        self.rest("ko", "<p><strong>테스트</strong></p>")

    def rest(self, lang, html):
        result = self.client.get(
            "/markedmodels/%s.json" % (self.instance.pk),
            HTTP_ACCEPT_LANGUAGE=lang,
        )
        self.assertIn('markdown', result.data)
        self.assertEqual(len(result.data['markdown']), 1)
        md = result.data['markdown'][0]
        self.assertEqual(md['type_label'], lang)
        self.assertEqual(md['html'], html)
