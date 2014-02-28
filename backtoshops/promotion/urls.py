import settings
from django.conf.urls.defaults import patterns, url
from promotion.views import CreatePromotionView, EditPromotionView, DeletePromotionView

urlpatterns = patterns(settings.get_site_prefix()+'promotion',
    url(r'/$', CreatePromotionView.as_view(), name="page_promotion"),
    url(r'/(?P<page>\d+)$', CreatePromotionView.as_view()),
    url(r'/(?P<pk>\d+)/edit$', EditPromotionView.as_view(), name="edit_promotion"),
    url(r'/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditPromotionView.as_view()),
    url(r'/(?P<pk>\d+)/delete$', DeletePromotionView.as_view(), name="delete_promotion"),
)

