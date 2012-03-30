from django.conf.urls.defaults import patterns, url
import settings
from views import *

urlpatterns = patterns(settings.SITE_NAME+'.backend',
    url(r'brands$', CreateBrandView.as_view(), name='sa_brands'),
    url(r'brands/(?P<pk>\d+)/edit$', EditBrandView.as_view(), name='sa_edit_brand'),
    url(r'brands/(?P<pk>\d+)/delete$', DeleteBrandView.as_view(), name='sa_delete_brand'),
    url(r'users$', CreateUserView.as_view(), name='sa_users'),
    url(r'users/(?P<pk>\d+)/edit$', EditUserView.as_view(), name='sa_edit_user'),
    url(r'users/(?P<pk>\d+)/delete$', DeleteUserView.as_view(), name='sa_delete_user'),
    url(r'ajax/user_search$',ajax_user_search, name='sa_ajax_user_search'),
    url(r'categories$', CreateCategoryView.as_view(), name='sa_categories'),
    url(r'categories/(?P<pk>\d+)/edit$', EditCategoryView.as_view(), name='sa_edit_category'),
    url(r'categories/(?P<pk>\d+)/delete$', DeleteCategoryView.as_view(), name='sa_delete_category'),
    url(r'attributes$', CreateAttributeView.as_view(), name='sa_attributes'),
    url(r'attributes/(?P<pk>\d+)/edit$', EditAttributeView.as_view(), name='sa_edit_attribute'),
    url(r'attributes/(?P<pk>\d+)/delete$', DeleteAttributeView.as_view(), name='sa_delete_attribute'),    
    url(r'brandings$', CreateBrandingView.as_view(), name='sa_brandings'),
    url(r'brandings/(?P<pk>\d+)/edit$', EditBrandingView.as_view(), name='sa_edit_branding'),
    url(r'brandings/(?P<pk>\d+)/delete$', DeleteBrandingView.as_view(), name='sa_delete_branding'),
)
