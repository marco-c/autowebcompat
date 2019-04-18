from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    path('', views.index, name='index'),
    path('ping', views.ping, name='ping'),
    path('logout', auth_views.LogoutView.as_view()),

    path('vote', views.vote, name='vote'),

    path('users', views.user_list, name='user_list'),
    path('users/<username>', views.user, name='user'),

    path('datasets', views.dataset_list, name='dataset_list'),
    path('datasets/<slug>', views.dataset, name='dataset'),

    path('sequences', views.sequence_list, name='sequence_list'),
    path('sequences/<int:pk>', views.sequence, name='sequence'),

    path('screenshots', views.screenshot_list, name='screenshots'),
    path('screenshots/<int:pk>', views.screenshot, name='screenshot'),
    path('img/<int:pk>.png', views.img, name='img'),

    path('submit_label', views.submit_label, name='submit_label'),
    path('decisions', views.decision_list, name='decision_list'),
    path('decisions/<int:pk>', views.decision, name='decision'),
    path('img/superposition/<int:pk>.png', views.img_superposition, name='img_superposition'),
    path('img/difference/<int:pk>.png', views.img_difference, name='img_difference'),

    path('networks', views.network_list, name='network_list'),
    path('networks/<int:pk>', views.network, name='network'),

    path('network-templates', views.network_template_list, name='network_template_list'),
    path('network-templates/<int:pk>', views.network_template, name='network_template'),
]
