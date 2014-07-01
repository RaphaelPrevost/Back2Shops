import settings
from common.data_access import data_access
from common.utils import get_brief_product_list
from common.utils import get_category_from_sales
from common.utils import get_product_default_display_price
from views.base import BaseHtmlResource
from B2SUtils.base_actor import as_list
from B2SUtils.errors import ValidationError
from B2SFrontUtils.constants import REMOTE_API_NAME


class TypeListResource(BaseHtmlResource):
    template = "product_list.html"

    def _on_get(self, req, resp, **kwargs):
        obj_id = kwargs.get('id_type')
        if not obj_id:
            raise ValidationError('ERR_ID')

        req._params['type'] = obj_id
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)

        return {'category': get_category_from_sales(sales),
                'product_list': get_brief_product_list(sales)}


class ProductListResource(BaseHtmlResource):
    template = "product_list.html"

    def _on_get(self, req, resp, **kwargs):
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)
        return {'category': dict(),
                'product_list': get_brief_product_list(sales)}


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
        price = ori_price = get_product_default_display_price(product_info)

        if price and product_info.get('discount'):
            discount_type = product_info.get('discount', {}).get('@type')
            discount_price = product_info.get('discount', {}).get('#text')
            product_info['display']['discount_type'] = discount_type
            product_info['display']['discount'] = discount_price
            if discount_type == 'fixed':
                price = float(ori_price) - float(discount_price)
            elif discount_type == 'ratio':
                price = float(ori_price) * (100 - float(discount_price)) / 100

        product_info['display']['price'] = price
        product_info['display']['ori_price'] = ori_price

        # type attributes
        ## if it uses type attribute price, don't display the type attribute
        ## which has no price.
        type_attrs = as_list(product_info.get('type', {}).get('attribute'))
        product_info['type']['attribute'] = type_attrs
        unified_price = product_info.get('price', {}).get('#text')
        if not unified_price:
            for type_attr in type_attrs:
                if not 'price' in type_attr or not float(type_attr['price'].get('#text', 0)):
                    product_info['type']['attribute'].remove(type_attr)

        ## Don't display the type attribute which has no quantity.
        stocks = as_list(product_info.get('available', {}).get('stocks'))
        for type_attr in type_attrs:
            stock = sum([sum(int(ss.get('#text', 0)) for ss in as_list(x.get('stock')))
                        for x in stocks
                        if x.get('@attribute') == type_attr.get('@id')])
            if stock <= 0 and type_attr in product_info['type']['attribute']:
                product_info['type']['attribute'].remove(type_attr)

        return {
            'product_info': product_info,
            'product_list': product_list,
        }
