import logging

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import path, include

from route_settings_builder.api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', api.urls),
    path('login/', LoginView.as_view(template_name='login_form.html', success_url='api/v1/docs'), name='login'),
]

if settings.CURRENT_BRANCH == 'dev':
    logging.warning('LOADED IN DEV MODE. ALL PATHS ARE IN /dev/ ZONE\n')
    urlpatterns = [path('dev/', include(urlpatterns))]
