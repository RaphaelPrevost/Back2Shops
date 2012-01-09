import settings
from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse
from shops.views import ShopCoordinates, CreateShopView, DeleteShopView, EditShopView

urlpatterns = patterns(settings.SITE_NAME+'.shops',
    url(r'/coordinates', ShopCoordinates.as_view(), name='shop_coordinates'),
    url(r'/(?P<pk>\d+)/delete$', DeleteShopView.as_view(), name="delete_shop"),
    url(r'/(?P<pk>\d+)/edit$', EditShopView.as_view(), name="edit_shop"),
    url(r'$', CreateShopView.as_view(), name="page_shops"),
)

    # url(r'/shop/(?:(?P<shop_id>\d+)/)?$', 
    #     ShopView.as_view(),
    #     name="shop"
    # ),
    # url(r'/shop/(?P<shop_id>\d+)/$',
    #     DeleteView.as_view(model=Shop, success_url=reverse("shop")),
    #     name="delete_shop"
    # ),
