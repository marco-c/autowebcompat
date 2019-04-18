from django.utils.html import format_html
from django.contrib.auth.models import User
import django_tables2

from . import models


class BaseTable(django_tables2.Table):
    def render_id(self, value, record):
        if hasattr(record, 'get_absolute_url'):
            return format_html('<a href="{}">{}</a>', record.get_absolute_url(), value)
        return value


class UserTable(BaseTable):
    github = django_tables2.Column("GitHub URL", orderable=False, accessor='username')
    label_count = django_tables2.Column("Labels Added", orderable=False, accessor='id')

    def render_github(self, record):
        name = record.get_username()
        url = 'https://github.com/' + name
        return format_html('<a href="{}">@{}</a>', url, name)

    def render_label_count(self, record, value):
        return models.Label.objects.filter(user=record).count()

    class Meta:
        prefix = 'user_'
        exclude = ('password', 'is_superuser', 'is_staff', 'is_active', 'email')
        model = User


class DatasetTable(BaseTable):
    class Meta:
        prefix = 'dataset_'
        model = models.Dataset


class SequenceTable(BaseTable):
    dataset = django_tables2.Column(linkify=True)

    class Meta:
        prefix = 'sequence_'
        exclude = ('definition',)
        model = models.Sequence


class ScreenshotTable(BaseTable):
    sequence = django_tables2.Column(linkify=True)
    filename = django_tables2.Column(linkify=('app:img', {"pk": django_tables2.A("pk")}))

    class Meta:
        prefix = 'screenshot_'
        exclude = ('browser_info', 'png',)
        model = models.Screenshot


class DecisionTable(BaseTable):
    pic_left = django_tables2.Column(linkify=True)
    pic_right = django_tables2.Column(linkify=True)

    class Meta:
        prefix = 'decision_'
        model = models.Decision


class NetworkTable(BaseTable):
    dataset = django_tables2.Column(linkify=True)
    template = django_tables2.Column(linkify=True)

    class Meta:
        prefix = 'network_'
        model = models.Network


class NetworkTemplateTable(BaseTable):
    class Meta:
        prefix = 'network_template_'
        model = models.NetworkTemplate


class LabelTable(BaseTable):
    user = django_tables2.Column(linkify=True)
    decision = django_tables2.Column(linkify=True)

    class Meta:
        prefix = 'label_'
        model = models.Label
