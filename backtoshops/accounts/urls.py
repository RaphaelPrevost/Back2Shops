import settings
from django.conf.urls.defaults import patterns, url
from views import CreateOperatorView, EditOperatorView, DeleteOperatorView

urlpatterns = patterns(settings.SITE_NAME+'.accounts',
    url(r'^operators/$', CreateOperatorView.as_view(), name='operators'),
    url(r'operators/(?P<pk>\d+)/edit/$', EditOperatorView.as_view(), name='edit_operator'),
    url(r'operators/(?P<pk>\d+)/delete/$', DeleteOperatorView.as_view(), name='delete_operator'), 
    )