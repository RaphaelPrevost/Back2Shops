import settings
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import get_brief_product_list
from common.utils import get_url_format
from views.base import BaseHtmlResource
from B2SUtils.errors import ValidationError
from B2SFrontUtils.constants import REMOTE_API_NAME


class CategoryListResource(BaseHtmlResource):
    template = "product_list.html"

    def _on_get(self, req, resp, **kwargs):
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)
        return {'product_list': get_brief_product_list(sales)}


class ProductListResource(BaseHtmlResource):
    template = "product_list.html"

    def _on_get(self, req, resp, **kwargs):
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)
        return {'product_list': get_brief_product_list(sales)}


class ProductInfoResource(BaseHtmlResource):
    template = "product_info.html"

    def _on_get(self, req, resp, **kwargs):
        obj_id = kwargs.get('id_sale')
        if not obj_id:
            raise ValidationError('ERR_ID')

        # all sales
        all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
        if not all_sales or obj_id not in all_sales:
            raise ValidationError('ERR_ID')

        # product info
        product_info = all_sales[obj_id]
        if not settings.PRODUCTION and not product_info.get('img'):
            product_info['img'] = '/img/dollar-exemple.jpg'

        product_info['variant'] = product_info.get('variant') if (isinstance(product_info.get('variant'), list) or product_info.get('variant') is None) else [product_info.get('variant')]

        # product list
        product_list = get_brief_product_list(all_sales)

        # price
        product_info['display'] = dict()
        price = ori_price = product_info.get('price').get('#text')

        if product_info.get('discount'):
            discount_type = product_info.get('discount').get('@type')
            if discount_type == 'fixed':
                price = product_info.get('discount').get('#text')
                product_info['display']['discount'] = ((float(ori_price) - float(price))/float(ori_price)) * 100
            if discount_type == 'ratio':
                product_info['display']['discount'] = product_info.get('discount').get('#text')
                price =  float(price) * (100 - float(product_info['display']['discount']))

        product_info['display']['price'] = price
        product_info['display']['ori_price'] = ori_price

        return {'product_info': product_info,
                'product_list': product_list,
                'prodlist_url_format': get_url_format(FRT_ROUTE_ROLE.PRDT_LIST)}
