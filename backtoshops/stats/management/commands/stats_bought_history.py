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
import ujson
import settings
import xmltodict

from stats.models import BoughtHistory
from stats.management.commands._base import StatsCommand

from B2SCrypto.utils import get_from_remote
from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import RESP_RESULT


class Command(StatsCommand):
    help = "Collect bought history information from user server"

    def handle(self, *args, **options):
        url = settings.STATS_BOUGHT_HISTORY

        try:
            data = get_from_remote(
                url,
                settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                settings.PRIVATE_KEY_PATH)

            data = xmltodict.parse(data)
            data = data['histories']
            histories = data.get('item', [])

            if not isinstance(histories, list):
                histories = [histories]

            handled_histories = []
            for history in histories:
                ht_id = history['@id']
                id_sale = history['id_sale']
                users_id = history['users_id']

                history = BoughtHistory.objects.filter(sale_id=id_sale)
                if history.exists():
                    history = history[0]
                    cur_users = set(ujson.loads(history.users))
                    cur_users.add(users_id)
                    history.users = ujson.dumps(cur_users)
                    history.save()
                else:
                    BoughtHistory.objects.create(
                        sale_id=id_sale,
                        users=ujson.dumps(set([users_id])))
                handled_histories.append(ht_id)

            self.send_feedback(handled_histories)
        except Exception, e:
            logging.error('stats_visitors_handle_err: %s',
                          e,
                          exc_info=True)

    def send_feedback(self, handled_histories):
        if not handled_histories:
            return
        histories = {'id_list': handled_histories}
        try:
            data = self._send_feedback(settings.STATS_BOUGHT_HISTORY,
                                       histories)
            r = data['histories']['res']
            assert r == RESP_RESULT.S
        except Exception, e:
            logging.error('stats_bought_history_feedback_err: %s',
                          e,
                          exc_info=True)
