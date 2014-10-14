import logging
import urllib
import ujson
import settings
import xmltodict

from datetime import datetime, timedelta
from optparse import make_option
from django.core.management.base import BaseCommand
from stats.models import Incomes

from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote
from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import RESP_RESULT


DT_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

class Command(BaseCommand):
    help = "Collect incomes statistics information from user server"
    option_list = BaseCommand.option_list + (
        make_option(
            '-f', '--from',
            action='store',
            type='string',
            dest='from',
            default=str(datetime.utcnow().date())),
        make_option(
            '-t', '--to',
            action='store',
            type='string',
            dest='to',
            default=str((datetime.utcnow() + timedelta(days=1)).date())),
    )

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
        data = gen_encrypt_json_context(
            ujson.dumps(orders),
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH)
        try:
            resp = get_from_remote(
                settings.STATS_INCOME,
                settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                settings.PRIVATE_KEY_PATH,
                data=data,
                headers={'Content-Type': 'application/json'})
            data = xmltodict.parse(resp)
            r = data['incomes']['res']
            assert r == RESP_RESULT.S
        except Exception, e:
            logging.error('stats_incomes_feedback_err: %s',
                          e,
                          exc_info=True)



