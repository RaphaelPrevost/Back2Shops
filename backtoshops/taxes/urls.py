import settings
from django.conf.urls import patterns, url
from fouillis.views import super_admin_required

from taxes.views import get_rates

urlpatterns = patterns(settings.get_site_prefix()+'taxes',
    url(r'/get_rates/(?P<rid>\S+)$',
        super_admin_required(get_rates, login_url="bo_login"), name="get_rates"),
)
