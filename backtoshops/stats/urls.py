import settings
from django.conf.urls.defaults import patterns, url

from fouillis.views import operator_upper_required
from stats.views import StatsIncomesView


urlpatterns = patterns(settings.get_site_prefix()+'stats',
    url(r'/incomes$',
        operator_upper_required(StatsIncomesView.as_view(),
                                login_url="bo_login",
                                super_allowed=True),
        name='incomes_stats'),
)

