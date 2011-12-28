from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from sales.views import add_sale, BrandLogoView, edit_sale, ListSalesView, ProductBrandView, SaleDetails, SaleDetailsShop, SaleWizardNew, UploadProductPictureView
from sales.forms import ProductForm, ShopForm, StockFormset, TargetForm
import settings

forms = [
    (SaleWizardNew.STEP_SHOP, ShopForm),
    (SaleWizardNew.STEP_PRODUCT, ProductForm),
    (SaleWizardNew.STEP_STOCKS, StockFormset),
    (SaleWizardNew.STEP_TARGET, TargetForm)
]

urlpatterns = patterns(settings.SITE_NAME+'.sales',
    url(r'/picture/new/$',
        UploadProductPictureView.as_view(),
        name="upload_product_picture"),
    url(r'/brand/new/$',
        ProductBrandView.as_view(),
        name="add_new_brand"),
    url(r'/brand/logo/(?:(?P<brand_id>\d+)/)?$',
        BrandLogoView.as_view(),
        name="get_brand_logo"),
    url(r'/added/$', TemplateView.as_view(template_name="added.html"), name="sale_added"),
    url(r'/updated/$', TemplateView.as_view(template_name="updated.html"), name="sale_updated"),
    url(r'/new/(?:(?P<step>.+)/)?$',
        add_sale,
        name="add_sale"),
    url(r'/edit/(?P<sale_id>\d+)/(?:(?P<step>.+)/)?$',
        edit_sale,
        name="edit_sale"),
    url(r'/list/(?:(?P<sales_type>.+)/)?$',
        login_required(ListSalesView.as_view(), login_url="bo_login"),
        name='list_sales'),
    url(r'/details/(?:(?P<sale_id>\d+)/)?(?:(?P<shop_id>\d+)/)?$',
        SaleDetails.as_view(),
        name='sale_details'),
    url(r'/details_shop/(?:(?P<sale_id>\d+)/)?$',
        SaleDetailsShop.as_view(),
        name='sale_details_shop'),
)