import settings
import ujson
from common.constants import FRT_ROUTE_ROLE
from common.constants import CURR_USER_BASKET_COOKIE_NAME
from common.data_access import data_access
from common.redis_utils import get_redis_cli
from common.utils import get_brief_product
from common.utils import get_brief_product_list
from common.utils import get_url_format
from common.utils import generate_random_key
from views.base import BaseHtmlResource
from views.base import BaseJsonResource
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import USER_BASKET
from B2SProtocol.constants import USER_BASKET_COOKIE_NAME
from B2SUtils.common import get_cookie_value
from B2SUtils.common import set_cookie
from B2SUtils.errors import ValidationError
from B2SFrontUtils.constants import REMOTE_API_NAME


def get_basket(req, resp, cookie_name=None):
    basket_key = None
    basket_data = None
    if cookie_name:
        iternames = [cookie_name]
    else:
        iternames = [CURR_USER_BASKET_COOKIE_NAME, USER_BASKET_COOKIE_NAME]
    for c_name in iternames:
        basket_key = get_cookie_value(req, c_name)
        try:
            if basket_key:
                basket_data = get_redis_cli().get(basket_key)
                if basket_data: break
        except:
            pass

    if not basket_key:
        basket_key = USER_BASKET % generate_random_key()
        set_cookie(resp, USER_BASKET_COOKIE_NAME, basket_key)
    basket_data = ujson.loads(basket_data) if basket_data else {}
    return basket_key, basket_data

def clear_basket(req, resp, basket_key, basket_data):
    # called after the order placed successfully

    redis_cli = get_redis_cli()
    if basket_key == get_cookie_value(req, USER_BASKET_COOKIE_NAME):
        redis_cli.set(basket_key, ujson.dumps({}))

    elif basket_key == get_cookie_value(req, CURR_USER_BASKET_COOKIE_NAME):
        redis_cli.delete(basket_key)

        prev_basket_key, prev_basket_data = get_basket(req, resp, USER_BASKET_COOKIE_NAME)
        [prev_basket_data.pop(item) for item in basket_data
                                    if item in prev_basket_data]
        redis_cli.set(prev_basket_key, ujson.dumps(prev_basket_data))

    set_cookie(resp, CURR_USER_BASKET_COOKIE_NAME, "")

def _get_valid_attr(attrlist, attr_id):
    if not attr_id or not attrlist:
        return {}

    if attrlist and not isinstance(attrlist, list):
        attrlist = [attrlist]
    for attr in attrlist:
        if attr['@id'] == str(attr_id):
            return attr
    return {}


class BasketResource(BaseHtmlResource):
    template = "basket.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        basket_key, basket_data = get_basket(req, resp)
        # basket_data dict:
        # - key is json string
        #   {"id_sale": **, "id_shop": **, "id_attr": **, "id_variant": **}
        # - value is quantity

        all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
        basket = []
        for item, quantity in basket_data.iteritems():
            item_info = ujson.loads(item)
            id_sale = str(item_info['id_sale'])
            if id_sale not in all_sales:
                continue

            sale_info = all_sales[id_sale]
            basket.append({
                'item': item,
                'quantity': quantity,
                'variant': _get_valid_attr(
                            sale_info.get('variant'),
                            item_info.get('id_variant')),
                'type': _get_valid_attr(
                            sale_info.get('type', {}).get('attribute'),
                            item_info.get('id_attr')),
                'product': get_brief_product(sale_info)
            })
        return {
            'basket': basket,
            'product_list': get_brief_product_list(all_sales),
            'err': req.get_param('err') or '',
        }


class BasketAPIResource(BaseJsonResource):
    def _on_post(self, req, resp, **kwargs):
        basket_key, basket_data = get_basket(req, resp)

        cmd = req.get_param('cmd')
        quantity = req.get_param('quantity') or 1
        chosen_item = req.get_param('sale')
        if not chosen_item:
            id_sale = req.get_param('id_sale')
            all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
            attr = _get_valid_attr(
                            all_sales[id_sale].get('type', {}).get('attribute'),
                            req.get_param('id_attr'))
            chosen_item = {'id_sale': id_sale,
                           'id_shop': req.get_param('id_shop') or 0,
                           'id_variant': req.get_param('id_variant'),
                           'id_attr': req.get_param('id_attr')
                                      if 'weight' in attr else 0,
                           'id_price_type': req.get_param('id_attr')
                                            if 'price' in attr else 0,
                           }
            chosen_item = ujson.dumps(chosen_item)

        if cmd == 'add':
            if chosen_item in basket_data:
                basket_data[chosen_item] += int(quantity)
            else:
                basket_data[chosen_item] = int(quantity)

        elif cmd == 'update':
            basket_data[chosen_item] = int(quantity)

        elif cmd == 'del':
            if chosen_item in basket_data:
                del basket_data[chosen_item]
        else:
            raise ValidationError('ERR_CMD')

        basket_data.update(basket_data)
        get_redis_cli().set(basket_key, ujson.dumps(basket_data))
        return {}
