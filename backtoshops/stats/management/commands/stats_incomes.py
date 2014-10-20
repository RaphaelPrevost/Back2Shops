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



