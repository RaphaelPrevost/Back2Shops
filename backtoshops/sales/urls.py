import settings
from django.conf.urls import patterns, url
from fouillis.views import manager_upper_required
from fouillis.views import operator_upper_required
from fouillis.views import shop_manager_upper_required
from django.views.generic.base import TemplateView

from sales.views import BrandLogoView
from sales.views import DeleteSalesView
from sales.views import ListSalesView
from sales.views import ProductBrandView
from sales.views import SaleDetails
from sales.views import SaleDetailsShop
from sales.views import UploadProductPictureView
from sales.views import add_sale
from sales.views import edit_sale
from sales.views import get_product_types


urlpatterns = patterns(settings.get_site_prefix()+'sales',
    url(r'/picture/new/$',
        UploadProductPictureView.as_view(),
        name="upload_product_picture"),
    url(r'/brand/new/$',
        ProductBrandView.as_view(),
        name="add_new_brand"),
    url(r'/brand/logo/(?:(?P<brand_id>\d+)/)?$',
        BrandLogoView.as_view(),
        name="get_brand_logo"),
    url(r'/added/$',
        TemplateView.as_view(template_name="added.html"),
        name="sale_added"),
    url(r'/updated/$',
        TemplateView.as_view(template_name="updated.html"),
        name="sale_updated"),
    url(r'/new/(?:(?P<step>.+)/)?$',
        add_sale,
        name="add_sale"),
    url(r'/edit/(?P<sale_id>\d+)/(?:(?P<step>.+)/)?$',
        edit_sale,
        name="edit_sale"),
    url(r'/list/(?:(?P<sales_type>.+)/)?$',
        operator_upper_required(ListSalesView.as_view(), login_url="/"),
        name='list_sales'),
    url(r'/details/(?:(?P<sale_id>\d+)/)?(?:(?P<shop_id>\d+)/)?$',
        SaleDetails.as_view(),
        name='sale_details'),
    url(r'/details_shop/(?:(?P<sale_id>\d+)/)?$',
        SaleDetailsShop.as_view(),
        name='sale_details_shop'),
    url(r'/delete/(?P<sale_id>\d+)',
        shop_manager_upper_required(DeleteSalesView.as_view(), login_url="/"),
        name='delete_sales'),
    url(r'/get_product_types/(?P<cat_id>\d+)',
        manager_upper_required(get_product_types, login_url="/"),
        name='get_product_types'),
)
