import settings
import ujson
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.redis_utils import get_redis_cli
from common.utils import get_brief_product
from common.utils import get_cookie_value
from common.utils import get_url_format
from common.utils import generate_random_key
from common.utils import set_cookie
from views.base import BaseHtmlResource
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import USER_BASKET
from B2SProtocol.constants import USER_BASKET_COOKIE_NAME
from B2SUtils.errors import ValidationError
from B2SFrontUtils.constants import REMOTE_API_NAME


class BasketResource(BaseHtmlResource):
    template = "basket.html"

    def _on_get(self, req, resp, **kwargs):
        brand = settings.BRAND_ID
        basket_key, basket_data = self._get_basket(req, resp)
        # basket_data: key is sale id + attributes, value is quantity

        all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
        basket = []
        for item, quantity in basket_data.iteritems():
            item_info = ujson.loads(item)
            id_sale = item_info['id_sale']
            if id_sale not in all_sales:
                continue
            basket.append({'item': item_info,
                           'quantity': quantity,
                           'product': get_brief_product(all_sales[id_sale])})
        return {'basket': basket}

    def _on_post(self, req, resp, **kwargs):
        basket_key, basket_data = self._get_basket(req, resp)

        cmd = req.get_param('cmd')
        id_sale = req.get_param('id_sale')
        if not id_sale:
            raise ValidationError('ERR_SALE')
        item_params = req._params.copy()
        item_params.pop('cmd')
        chosen_item = ujson.dumps(item_params)

        if cmd == 'add':
            if chosen_item not in basket_data:
                basket_data[chosen_item] = 0
            basket_data[chosen_item] += 1

        elif cmd == 'del':
            if chosen_item in basket_data:
                if basket_data[chosen_item] == 1:
                    basket_data.remove(chosen_item)
                else:
                    basket_data[chosen_item] -= 1
        else:
            raise ValidationError('ERR_CMD')

        basket_data.update(basket_data)
        get_redis_cli().setex(basket_key, ujson.dumps(basket_data), 3600*24)

        self.redirect(get_url_format(FRT_ROUTE_ROLE.BASKET))


    def _get_basket(self, req, resp):
        basket_key = get_cookie_value(req, USER_BASKET_COOKIE_NAME)
        basket_data = None
        if basket_key:
            try:
                basket_data = get_redis_cli().get(basket_key)
            except:
                pass
        else:
            basket_key = USER_BASKET % generate_random_key()
            set_cookie(resp, USER_BASKET_COOKIE_NAME, basket_key)
        basket_data = ujson.loads(basket_data) if basket_data else {}
        return basket_key, basket_data

