from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('social_django.urls', namespace='social')),
    path('admin/', admin.site.urls),
    path('', include('app.urls', namespace='app')),
]
