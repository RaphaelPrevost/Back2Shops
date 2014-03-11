import settings
from django.conf.urls import patterns, url
from countries.views import get_country_states
from fouillis.views import operator_upper_required

urlpatterns = patterns(settings.get_site_prefix()+'countries',
    url(r'/get_states/(?P<cid>\S+)$',
        operator_upper_required(get_country_states, login_url="bo_login"),
        name="get_country_states"),
)
