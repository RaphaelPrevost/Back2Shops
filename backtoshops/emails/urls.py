import settings
from django.conf.urls import patterns, url
from fouillis.views import admin_required
from emails.views import *

urlpatterns = patterns(settings.get_site_prefix() + 'emails',
   url(r'/images/new/$',
       UploadEmailImageView.as_view(), name="upload_email_image"),

   url(r'/$',
       admin_required(NewTemplateView.as_view()), name="new_template"),
   url(r'/(?P<page>\d+)$',
       admin_required(NewTemplateView.as_view()), name="new_template"),

   url(r'/(?P<pk>\d+)/edit$',
       admin_required(EditTemplateView.as_view()), name="edit_template"),
   url(r'/(?P<pk>\d+)/edit/(?P<page>\d+)$',
       admin_required(EditTemplateView.as_view()), name="edit_template"),
   url(r'/(?P<pk>\d+)/preview$',
       admin_required(PreviewTemplateContentView.as_view()), name="preview_template"),

   url(r'/(?P<pk>\d+)/delete$',
       admin_required(DeleteTemplateView.as_view()), name="delete_template"),

)
