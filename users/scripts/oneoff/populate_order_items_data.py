# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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


import ujson
import settings

from collections import defaultdict
from common.utils import remote_xml_shipping_services
from models.actors.sale import CachedSale
from B2SUtils.db_utils import select_dict, get_conn, update
from B2SUtils.db_utils import init_db_pool
from B2SUtils.base_actor import actor_to_dict


init_db_pool(settings.DATABASE)

def populate_order_items():

    with get_conn() as conn:
        r = select_dict(conn, "order_items", 'id')
        for item_id, item in r.iteritems():
            id_sale = item['id_sale']
            sale = CachedSale(id_sale).sale
            if not sale:
                print 'no cached sale for: ', id_sale, 'please populate data manually'
                continue

            values = {'weight_unit': sale.weight_unit,
                      'currency': sale.price.currency}

            id_weight_type = item['id_weight_type']
            if id_weight_type:
                weight_detail = sale.get_weight_attr(id_weight_type)
                values['weight'] = weight_detail.weight.value
                values['weight_type_detail'] = ujson.dumps(actor_to_dict(weight_detail))
            else:
                values['weight'] = sale.standard_weight

            id_variant = item['id_variant']
            if id_variant:
                variant = sale.get_variant(id_variant)
                variant_detail = ujson.dumps(actor_to_dict(variant))
                values['variant_detail'] = variant_detail

            values['item_detail'] = ujson.dumps(actor_to_dict(sale))

            update(conn, 'order_items', values=values, where={'id': item['id']})
            print "update order items ", item['id'], 'with values', values


def poplate_supported_services():

    with get_conn() as conn:
        r = select_dict(conn, 'shipping_supported_services', 'id')
        for item_id, item in r.iteritems():
            supported_services = item['supported_services']
            supported_services = ujson.loads(supported_services)
            carrier_services_map = defaultdict(list)
            for id_service, id_carrier in supported_services.iteritems():
                carrier_services_map[id_carrier].append(id_service)
            supported_services_details = remote_xml_shipping_services(
                carrier_services_map.items())
            values = {'supported_services_details': supported_services_details}
            update(conn, 'shipping_supported_services', values=values)

            print "update supported services details ", item['id'], 'with values', values


if __name__ == "__main__":
    populate_order_items()
    poplate_supported_services()



