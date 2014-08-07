import settings
import ujson
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.redis_utils import get_redis_cli
from common.utils import get_basket
from common.utils import get_basket_table_info
from common.utils import get_brief_product
from common.utils import get_brief_product_list
from common.utils import get_url_format
from common.utils import generate_random_key
from common.utils import get_valid_attr
from views.base import BaseHtmlResource
from views.base import BaseJsonResource
from B2SUtils.errors import ValidationError
from B2SFrontUtils.constants import REMOTE_API_NAME


class BasketResource(BaseHtmlResource):
    template = "basket.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        _, basket_data = get_basket(req, resp)
        return {
            'basket': get_basket_table_info(req, resp, basket_data),
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
            attr = get_valid_attr(
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
