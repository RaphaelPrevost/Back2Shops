import settings
from django.conf.urls.defaults import patterns, url
from brandings.views import CreateBrandingView, EditBrandingView, \
    DeleteBrandingView

urlpatterns = patterns(settings.get_site_prefix()+'brandings',
    url(r'/$', CreateBrandingView.as_view(), name="page_brandings"),
    url(r'/(?P<page>\d+)$', CreateBrandingView.as_view()),
    url(r'/(?P<pk>\d+)/edit$', EditBrandingView.as_view(), name="edit_branding"),
    url(r'/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditBrandingView.as_view()),
    url(r'/(?P<pk>\d+)/delete$', DeleteBrandingView.as_view(), name="delete_branding"),
)

