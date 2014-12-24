# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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


import logging
import ujson

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SUtils.errors import ValidationError
from common.data_access import data_access
from common.redis_utils import get_redis_cli
from common.utils import get_basket
from common.utils import get_basket_table_info
from common.utils import get_valid_attr
from common.utils import unescape_string
from views.base import BaseHtmlResource
from views.base import BaseJsonResource


class BasketResource(BaseHtmlResource):
    template = "basket.html"
    show_products_menu = False

    def _on_get(self, req, resp, **kwargs):
        _, basket_data = get_basket(req, resp)
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)
        return {
            'basket': get_basket_table_info(req, resp, basket_data,
                                            self.users_id),
            'err': req.get_param('err') or '',
        }


class BasketAPIResource(BaseJsonResource):

    def _on_get(self, req, resp, **kwargs):
        basket_key, basket_data = get_basket(req, resp)
        for quantity in basket_data.itervalues():
            try:
                if int(quantity) <= 0:
                    raise ValidationError('ERR_QUANTITY')
            except:
                raise ValidationError('ERR_QUANTITY')
        return {}

    def _on_post(self, req, resp, **kwargs):
        basket_key, basket_data = get_basket(req, resp)

        cmd = req.get_param('cmd')
        quantity = req.get_param('quantity') or '1'
        if not isinstance(quantity, str) or not quantity.isdigit():
            raise ValidationError('ERR_QUANTITY')
        quantity = int(quantity)

        chosen_item = req.get_param('sale')
        if not chosen_item:
            id_sale = req.get_param('id_sale')
            all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
            if id_sale not in all_sales:
                logging.error('Wrong request id_sale %s for basket, cmd: %s',
                              id_sale, cmd)
                return {}
            attr = get_valid_attr(
                all_sales[id_sale].get('type', {}).get('attribute'),
                req.get_param('id_attr'))
            chosen_item = {'id_sale': id_sale,
                           'id_shop': req.get_param('id_shop') or 0,
                           'id_variant': req.get_param('id_variant'),
                           'id_attr': req.get_param('id_attr'),
                           'id_weight_type': req.get_param('id_attr')
                                      if 'weight' in attr else 0,
                           'id_price_type': req.get_param('id_attr')
                                            if 'price' in attr else 0,
                           }
            chosen_item = ujson.dumps(chosen_item)
        else:
            chosen_item = unescape_string(chosen_item)

        if cmd == 'add':
            if chosen_item in basket_data:
                basket_data[chosen_item] += quantity
            else:
                basket_data[chosen_item] = quantity

        elif cmd == 'update':
            basket_data[chosen_item] = quantity

        elif cmd == 'del':
            if chosen_item in basket_data:
                del basket_data[chosen_item]
        else:
            raise ValidationError('ERR_CMD')

        basket_data.update(basket_data)
        get_redis_cli().set(basket_key, ujson.dumps(basket_data))
        return {}
