# I'm too lazy to add the specific error codes for star imports
# and unknown references (F403, F405), so:
# flake8: noqa
from django.contrib import admin
from django.utils.safestring import mark_safe
# from django.contrib.auth.models import User

from .models import *


class DatasetAdmin(admin.ModelAdmin):
    pass


class SequenceAdmin(admin.ModelAdmin):
    readonly_fields = ('dataset',)


class ScreenshotAdmin(admin.ModelAdmin):
    readonly_fields = ('filename', 'sequence', 'browser_name', 'img')

    def img(self, instance):
        url = instance.get_image_url()
        return mark_safe(f'<img src="{url}" height="80%" />')


class DecisionAdmin(admin.ModelAdmin):
    readonly_fields = ('pic_left', 'pic_right', 'key', 'images')

    def images(self, instance):
        url_left = instance.pic_left.get_absolute_url()
        url_right = instance.pic_right.get_absolute_url()
        return mark_safe(f'<div><img src="{url_left}" height="80%"/><img src="{url_right}" height="80%"/></div>')

    def img_right(self, instance):
        return inline_img(instance.pic_right)


class LabelAdmin(admin.ModelAdmin):
    readonly_fields = ('user', 'decision')


class NetworkTemplateAdmin(admin.ModelAdmin):
    pass


class NetworkAdmin(admin.ModelAdmin):
    readonly_fields = ('dataset', 'template')


class PredictionAdmin(admin.ModelAdmin):
    readonly_fields = ('network', 'model')


admin.site.register(Dataset, DatasetAdmin)
admin.site.register(Sequence, SequenceAdmin)
admin.site.register(Screenshot, ScreenshotAdmin)
admin.site.register(Decision, DecisionAdmin)
admin.site.register(Label, LabelAdmin)
admin.site.register(NetworkTemplate, NetworkTemplateAdmin)
admin.site.register(Network, NetworkAdmin)
admin.site.register(Prediction, PredictionAdmin)
