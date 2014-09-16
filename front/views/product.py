import settings

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SUtils.base_actor import as_list
from B2SUtils.errors import ValidationError
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import get_category_taxrate
from common.utils import get_discounted_price
from common.utils import get_brief_product_list
from common.utils import get_category_from_sales
from common.utils import get_normalized_name
from common.utils import get_product_default_display_price
from common.utils import get_random_products
from common.utils import get_type_from_sale
from common.utils import get_url_format
from common.utils import is_routed_template
from views.base import BaseHtmlResource


class TypeListResource(BaseHtmlResource):
    template = "product_list.html"
    cur_tab_index = 0
    role = FRT_ROUTE_ROLE.TYPE_LIST

    def _on_get(self, req, resp, **kwargs):
        is_routed = is_routed_template(self.role)
        type_id = kwargs.get('id_type')
        if not type_id:
            raise ValidationError('ERR_ID')

        type_name = ''
        if is_routed:
            type_name = kwargs.get('type_name')
            if not type_name:
                raise ValidationError('ERR_NAME')

        req._params['type'] = type_id
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)

        if is_routed:
            type_info = get_type_from_sale(sales and sales.values()[0] or {})
            normalized_type_name = get_normalized_name(
                FRT_ROUTE_ROLE.TYPE_LIST,
                'type_name',
                type_info['name'])
            if type(normalized_type_name) == unicode:
                normalized_type_name = normalized_type_name.encode('UTF-8')
            if normalized_type_name != type_name:
                self.redirect(get_url_format(FRT_ROUTE_ROLE.TYPE_LIST) % {
                    'id_type': type_id, 'type_name': normalized_type_name
                })
                return

        return {'cur_type_id': type_id,
                'category': get_category_from_sales(sales),
                'product_list': get_brief_product_list(sales)}


class ProductListResource(BaseHtmlResource):
    template = "product_list.html"
    cur_tab_index = 0

    def _on_get(self, req, resp, **kwargs):
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)
        return {'category': dict(),
                'product_list': get_random_products(sales)}


class ProductInfoResource(BaseHtmlResource):
    template = "product_info.html"
    cur_tab_index = 0
    role = FRT_ROUTE_ROLE.PRDT_INFO

    def _on_get(self, req, resp, **kwargs):
        is_routed = is_routed_template(self.role)
        sale_id = kwargs.get('id_sale')
        if not sale_id:
            raise ValidationError('ERR_ID')

        sale_name = type_id = type_name = None
        if is_routed:
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
        product_info = all_sales[sale_id]

        if is_routed:
            type_info = get_type_from_sale(product_info)
            normalized_type_name = get_normalized_name(
                FRT_ROUTE_ROLE.PRDT_INFO,
                'type_name',
                type_info['name'])
            normalized_sale_name = get_normalized_name(
                FRT_ROUTE_ROLE.PRDT_INFO,
                'sale_name',
                product_info.get('name', ''))
            if type(normalized_type_name) is unicode:
                normalized_type_name = normalized_type_name.encode('UTF-8')
            if type(normalized_sale_name) is unicode:
                normalized_sale_name = normalized_sale_name.encode('UTF-8')
            if normalized_type_name != type_name or \
                    normalized_sale_name != sale_name:
                self.redirect(get_url_format(FRT_ROUTE_ROLE.PRDT_INFO) % {
                    'id_type': type_id, 'type_name': normalized_type_name,
                    'id_sale': sale_id, 'sale_name': normalized_sale_name,
                })
                return

        # product info
        if not settings.PRODUCTION and not product_info.get('img'):
            product_info['img'] = '/img/dollar-example.jpg'

        product_info['variant'] = as_list(product_info.get('variant'))

        # price
        product_info['display'] = dict()
        price = ori_price = get_product_default_display_price(product_info)

        if price and product_info.get('discount'):
            price, discount_type, discount_price = \
                    get_discounted_price(price, product_info)
            product_info['display']['discount_type'] = discount_type
            product_info['display']['discount'] = discount_price
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

        taxes_rate = {}
        _cate_id = product_info.get('category', {}).get('@id', 0)
        shops = dict([(node['@id'], node)
                      for node in as_list(product_info.get('shop'))])
        shops.update({"0": product_info.get('brand', {})})
        for _id, node in shops.iteritems():
            addr = node.get('address', {}).get('country')
            if addr and addr.get("#text"):
                country_code = addr["#text"]
                province_code = addr.get("@province")
                category_tax = get_category_taxrate(req, resp,
                                   country_code, province_code, _cate_id)
                taxes_rate[_id] = category_tax

        return {
            'cur_type_id': type_id,
            'product_info': product_info,
            'product_list': get_random_products(all_sales),
            'taxes_rate': taxes_rate,
        }
