import settings
from django.conf.urls.defaults import patterns, url
from users_webservice.views import create_user

urlpatterns = patterns(settings.SITE_NAME,
    url(r'1.0/pub/account', create_user),
)
