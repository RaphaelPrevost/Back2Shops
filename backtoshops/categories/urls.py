import settings
from django.conf.urls.defaults import patterns, url
from categories.views import CreateCategoryView, EditCategoryView, DeleteCategoryView

urlpatterns = patterns(settings.get_site_prefix()+'categories',
    url(r'/new/$', CreateCategoryView.as_view(), name='list_categories'),
    url(r'/(?P<page>\d+)$', CreateCategoryView.as_view()),
    url(r'/(?P<pk>\d+)/edit/$', EditCategoryView.as_view(), name='edit_category'),
    url(r'/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditCategoryView.as_view()),
    url(r'/(?P<pk>\d+)/delete/$', DeleteCategoryView.as_view(), name='delete_category'),
)

