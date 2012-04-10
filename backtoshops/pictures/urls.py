import settings
from django.conf.urls.defaults import patterns, url
from pictures.views import UploadProductPictureView

urlpatterns = patterns(settings.get_site_prefix()+'pictures',
    url(r'/picture/new/$',
        UploadProductPictureView.as_view(),
        name="upload_product_picture"),
)