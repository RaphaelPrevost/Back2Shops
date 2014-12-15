import settings
from django.conf.urls.defaults import patterns, url
from producttypes.views import CreateProductTypeView, EditProductTypeView, \
    EditProductTypeView, DeleteProductTypeView, UpdateProductTypeOrderView


urlpatterns = patterns(settings.get_site_prefix()+'producttypes',
    url(r'/new/$', CreateProductTypeView.as_view(), name='page_producttypes'),
    url(r'/(?P<page>\d+)$', CreateProductTypeView.as_view()),
    url(r'/(?P<pk>\d+)/edit/$', EditProductTypeView.as_view(), name='edit_producttype'),
    url(r'/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditProductTypeView.as_view()),
    url(r'/(?P<pk>\d+)/delete/$', DeleteProductTypeView.as_view(), name='delete_producttype'),
    url(r'/sort$', UpdateProductTypeOrderView.as_view(), name='sort_producttypes'),
)

