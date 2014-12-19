# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


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
    url(r'/list/(?:(?P<sales_type>old)/)?$',
        manager_upper_required(ListSalesView.as_view(), login_url="/"),
        name='list_sales'),
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
