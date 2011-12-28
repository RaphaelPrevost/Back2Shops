import settings
from django.conf.urls.defaults import patterns, url
from pictures.views import UploadProductPictureView

urlpatterns = patterns(settings.SITE_NAME+'.pictures',
    url(r'/picture/new/$',
        UploadProductPictureView.as_view(),
        name="upload_product_picture"),
)