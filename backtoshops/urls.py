from django.conf.urls.defaults import patterns, include, url
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from accounts.views import home_page
import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = staticfiles_urlpatterns()
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^rosetta/', include('rosetta.urls')),
    )

urlpatterns += patterns('',
    url(r'^logout$', 'django.contrib.auth.views.logout', name='bo_logout')
)

urlpatterns += patterns('',
    url(r'^webservice', include(settings.SITE_NAME+'.webservice.urls')),
    url(r'^attributes', include(settings.SITE_NAME+'.attributes.urls')),
    url(r'^pictures', include(settings.SITE_NAME+'.pictures.urls')),
    url(r'^sales', include(settings.SITE_NAME+'.sales.urls')),
    url(r'^shops', include(settings.SITE_NAME+'.shops.urls')),
    url(r'^login', 'fouillis.views.login_staff', name='bo_login'),
    url(r'^$',
        login_required(home_page, login_url="login"),
        name='bo_index'),
    # Examples:
    # url(r'^$', 'backtoshops.views.home', name='home'),
    # url(r'^backtoshops/', include('backtoshops.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^setlang/','accounts.views.set_language'),
    url(r'^sa/', include(settings.SITE_NAME+'.backend.urls')),
)

