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


import logging
import urllib
import settings
import xmltodict

from stats.models import Incomes
from stats.management.commands._base import StatsCommand

from B2SCrypto.utils import get_from_remote
from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import RESP_RESULT



class Command(StatsCommand):
    help = "Collect incomes statistics information from user server"

    def handle(self, *args, **options):
        p = {'from': options['from'],
             'to': options['to']}
        p = urllib.urlencode(p)
        url = settings.STATS_INCOME + '?' + p

        try:
            data = get_from_remote(
                url,
                settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                settings.PRIVATE_KEY_PATH)

            data = xmltodict.parse(data)
            data = data['incomes']
            incomes = data.get('income', [])

            if not isinstance(incomes, list):
                incomes = [incomes]

            handled_orders = set()
            for income in incomes:
                Incomes.objects.create(
                    sale_id=income['id_sale'],
                    shop_id=income['id_shop'],
                    users_id=income['@id_user'],
                    variant_id=income['id_variant'],
                    price=income['price'],
                    quantity=income['quantity'],
                    up_time=income['@up_time'])
                handled_orders.add(income['@id_order'])

            self.send_feedback(handled_orders)
        except Exception, e:
            logging.error('stats_visitors_handle_err: %s',
                          e,
                          exc_info=True)

    def send_feedback(self, handled_orders):
        if not handled_orders:
            return
        orders = {'order_list': handled_orders}
        try:
            data = self._send_feedback(settings.STATS_INCOME, orders)
            r = data['incomes']['res']
            assert r == RESP_RESULT.S
        except Exception, e:
            logging.error('stats_incomes_feedback_err: %s',
                          e,
                          exc_info=True)



