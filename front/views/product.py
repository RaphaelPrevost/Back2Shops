import settings
import random

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SUtils.base_actor import as_list
from B2SUtils.errors import ValidationError
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import get_brief_product_list
from common.utils import get_category_from_sales
from common.utils import get_mapping_name
from common.utils import get_product_default_display_price
from common.utils import get_type_from_sales
from common.utils import get_url_format
from views.base import BaseHtmlResource


class TypeListResource(BaseHtmlResource):
    template = "product_list.html"

    def _on_get(self, req, resp, **kwargs):
        type_id = kwargs.get('id_type')
        if not type_id:
            raise ValidationError('ERR_ID')

        type_name = kwargs.get('type_name')
        if not type_name:
            raise ValidationError('ERR_NAME')

        req._params['type'] = type_id
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)
        type_info = get_type_from_sales(sales)
        mapping_type_name = get_mapping_name(FRT_ROUTE_ROLE.TYPE_LIST,
                                             'type_name',
                                             type_info['name'])
        if mapping_type_name != type_name:
            self.redirect(get_url_format(FRT_ROUTE_ROLE.TYPE_LIST) % {
                'id_type': type_id, 'type_name': mapping_type_name
            })
            return

        return {'category': get_category_from_sales(sales),
                'product_list': get_brief_product_list(sales)}


class ProductListResource(BaseHtmlResource):
    template = "product_list.html"

    def _on_get(self, req, resp, **kwargs):
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)
        random_sales = {}
        map(lambda k: random_sales.update({k: sales[k]}),
            random.sample(sales, settings.NUM_OF_RANDOM_SALES))
        return {'category': dict(),
                'product_list': get_brief_product_list(random_sales)}


class ProductInfoResource(BaseHtmlResource):
    template = "product_info.html"

    def _on_get(self, req, resp, **kwargs):
        sale_id = kwargs.get('id_sale')
        if not sale_id:
            raise ValidationError('ERR_ID')

        sale_name = kwargs.get('sale_name')
        if not sale_name:
            raise ValidationError('ERR_Name')
        
        type_id = kwargs.get('id_type')
        if not type_id:
            raise ValidationError('ERR_ID')

        type_name = kwargs.get('type_name')
        if not type_name:
            raise ValidationError('ERR_NAME')

        # all sales
        all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
        if not all_sales or sale_id not in all_sales:
            raise ValidationError('ERR_ID')

        # type info
        type_info = get_type_from_sales(all_sales)
        mapping_type_name = get_mapping_name(FRT_ROUTE_ROLE.PRDT_INFO,
                                             'type_name',
                                             type_info['name'])

        # product info
        product_info = all_sales[sale_id]
        mapping_sale_name = get_mapping_name(FRT_ROUTE_ROLE.PRDT_INFO,
                                             'sale_name',
                                             product_info.get('name', ''))

        if mapping_type_name != type_name or mapping_sale_name != sale_name:
            self.redirect(get_url_format(FRT_ROUTE_ROLE.PRDT_INFO) % {
                'id_type': type_id, 'type_name': mapping_type_name,
                'id_sale': sale_id, 'sale_name': mapping_sale_name,
            })
            return

        if not settings.PRODUCTION and not product_info.get('img'):
            product_info['img'] = '/img/dollar-example.jpg'

        product_info['variant'] = as_list(product_info.get('variant'))

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

        ## if it uses type attribute price, disable the type attribute
        ## which has no price.
        type_attrs = as_list(product_info.get('type', {}).get('attribute'))
        if 'type' in product_info:
            product_info['type']['attribute'] = type_attrs
        unified_price = product_info.get('price', {}).get('#text')
        if not unified_price:
            for type_attr in type_attrs:
                if (not 'price' in type_attr or
                        not float(type_attr['price'].get('#text', 0))):
                    type_attr['disabled'] = True

        ## Disable the type attribute which has no quantity.
        stocks = as_list(product_info.get('available', {}).get('stocks'))
        if 'available' in product_info:
            product_info['available']['stocks'] = stocks
            for stock in stocks:
                stock['stock'] = as_list(stock.get('stock'))
        for type_attr in type_attrs:
            stock = sum([sum(int(ss.get('#text', 0)) for ss in x.get('stock'))
                        for x in stocks
                        if x.get('@attribute') == type_attr.get('@id')])
            if stock <= 0:
                type_attr['disabled'] = True

        ## Disable the brand attribute which has no quantity.
        variants = as_list(product_info.get('variant'))
        product_info['variant'] = variants
        for var in variants:
            stock = sum([sum(int(ss.get('#text', 0)) for ss in x.get('stock'))
                        for x in stocks
                        if x.get('@variant') == var.get('@id')])
            if stock <= 0:
                var['disabled'] = True

        return {
            'product_info': product_info,
            'product_list': product_list,
        }
