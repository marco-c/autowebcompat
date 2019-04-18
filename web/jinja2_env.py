from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment

from app.models import Label


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': reverse,
        'LABEL_CHOICES': Label.LABEL_CHOICES,
    })
    return env
