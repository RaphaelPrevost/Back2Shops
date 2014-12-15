import settings
from django.conf.urls import patterns
from django.conf.urls import url
from backend.views import *

urlpatterns = patterns(settings.get_site_prefix()+'backend',
    url(r'brands/$', CreateBrandView.as_view(), name='sa_brands'),
    url(r'brands/(?P<page>\d+)$', CreateBrandView.as_view()),
    url(r'brands/(?P<pk>\d+)/edit/$', EditBrandView.as_view(), name='sa_edit_brand'),
    url(r'brands/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditBrandView.as_view()),
    url(r'brands/(?P<pk>\d+)/delete/$', DeleteBrandView.as_view(), name='sa_delete_brand'),
    url(r'users/$', CreateUserView.as_view(), name='sa_users'),
    url(r'users/(?P<pk>\d+)/edit/$', EditUserView.as_view(), name='sa_edit_user'),
    url(r'users/(?P<pk>\d+)/delete/$', DeleteUserView.as_view(), name='sa_delete_user'),
    url(r'ajax/user_search/$',ajax_user_search, name='sa_ajax_user_search'),
    url(r'settings/$', settings_view, name='sa_settings' ),

    url(r'carriers/$', CreateCarrierView.as_view(), name='sa_carriers'),
    url(r'carriers/(?P<page>\d+)$', CreateCarrierView.as_view()),
    url(r'carriers/(?P<pk>\d+)/edit/$', EditCarrierView.as_view(), name='sa_edit_carrier'),
    url(r'carriers/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditCarrierView.as_view()),
    url(r'carriers/(?P<pk>\d+)/delete/$', DeleteCarrierView.as_view(), name='sa_delete_carrier'),

    url(r'taxes/$', CreateTaxView.as_view(), name='sa_taxes'),
    url(r'taxes/(?P<page>\d+)$', CreateTaxView.as_view()),
    url(r'taxes/(?P<pk>\d+)/edit/$', EditTaxView.as_view(), name='sa_edit_tax'),
    url(r'taxes/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditTaxView.as_view()),
    url(r'taxes/(?P<pk>\d+)/delete/$', DeleteTaxView.as_view(), name='sa_delete_tax'),

)
