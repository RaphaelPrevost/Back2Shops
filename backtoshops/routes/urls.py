import settings
from django.conf.urls import patterns, url
from routes.views import *
from fouillis.views import admin_required


urlpatterns = patterns(settings.get_site_prefix() + 'routes',
   url(r'/get_page_roles/$', get_page_roles, name="get_page_roles"),
   url(r'/get_route_params/(?P<pid>\d+)$', get_route_params, name="get_route_params"),
   url(r'/$', CreateRouteView.as_view(), name="routes"),
   url(r'/(?P<page>\d+)$', CreateRouteView.as_view()),
   url(r'/(?P<pk>\d+)/edit$', admin_required(EditRouteView.as_view()), name="edit_route"),
   url(r'/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditRouteView.as_view()),
   url(r'/(?P<pk>\d+)/delete$', DeleteRouteView.as_view(), name="delete_route"),
)
