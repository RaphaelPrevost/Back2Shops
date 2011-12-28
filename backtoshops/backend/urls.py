from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
import settings

urlpatterns = patterns('',
    url(r'/logout/', 'django.contrib.auth.views.logout', name='bo_logout')
)

urlpatterns += patterns(settings.SITE_NAME+'.backend',
    url(r'/login/', 'views.login_staff', name='bo_login'),
    url(r'$',
        login_required(TemplateView.as_view(template_name="index.html"), login_url="login"),
        name='bo_index')
)
