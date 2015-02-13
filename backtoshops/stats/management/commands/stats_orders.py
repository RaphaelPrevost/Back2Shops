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


import logging
import urllib
import settings
import xmltodict

from stats.models import Orders
from stats.management.commands._base import StatsCommand

from B2SCrypto.utils import get_from_remote
from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import RESP_RESULT



class Command(StatsCommand):
    help = "Collect orders information from user server"

    def handle(self, *args, **options):
        p = {'from': options['from'],
             'to': options['to']}
        p = urllib.urlencode(p)
        url = settings.STATS_ORDER + '?' + p

        try:
            data = get_from_remote(
                url,
                settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                settings.PRIVATE_KEY_PATH)

            data = xmltodict.parse(data)
            data = data['orders']
            logs = data.get('log', [])

            if not isinstance(logs, list):
                logs = [logs]

            completed_logs = set()
            for log in logs:
                shop_id = int(log['id_shop'])
                if shop_id == 0:
                    shop_id = None
                obj, _ = Orders.objects.get_or_create(
                    users_id=log['users_id'],
                    order_id=log['id_order'],
                    brand_id=log['id_brand'],
                    shop_id=shop_id)
                obj.pending_date = log['pending_date']
                obj.waiting_payment_date = log['waiting_payment_date']
                obj.waiting_shipping_date = log['waiting_shipping_date']
                obj.completed_date = log['completed_date']
                obj.save()

                if log['completed_date']:
                    completed_logs.add(log['@id'])

            self.send_feedback(completed_logs)
        except Exception, e:
            logging.error('stats_visitors_handle_err: %s',
                          e,
                          exc_info=True)

    def send_feedback(self, handled_logs):
        if not handled_logs:
            return
        logs = {'id_list': handled_logs}
        try:
            data = self._send_feedback(settings.STATS_ORDER, logs)
            r = data['orders']['res']
            assert r == RESP_RESULT.S
        except Exception, e:
            logging.error('stats_orders_feedback_err: %s',
                          e,
                          exc_info=True)
