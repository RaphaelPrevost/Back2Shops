import settings
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from countries.views import get_country_states

urlpatterns = patterns(settings.get_site_prefix()+'countries',
    url(r'/get_states/(?P<cid>\S+)$',
        login_required(get_country_states, login_url="bo_login"),
        name="get_country_states"),
)
