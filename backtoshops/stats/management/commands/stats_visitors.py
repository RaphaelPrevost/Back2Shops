import logging
import urllib
import ujson
import settings
import xmltodict

from datetime import datetime, timedelta
from optparse import make_option
from django.core.management.base import BaseCommand
from stats.models import Visitors

from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote
from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import RESP_RESULT


DT_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

class Command(BaseCommand):
    help = "Collect visitors statistics information from user server"
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
        url = settings.STATS_VISITORS + '?' + p

        try:
            data = get_from_remote(
                url,
                settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                settings.PRIVATE_KEY_PATH)

            data = xmltodict.parse(data)
            data = data['visitors']
            users = data.get('user', [])

            if not isinstance(users, list):
                users = [users]

            for user in users:
                Visitors.objects.create(
                    sid=user['@sid'],
                    users_id=user['users_id'],
                    visit_time=user['visit_time'])

            self.send_feedback(users)
        except Exception, e:
            logging.error('stats_visitors_handle_err: %s',
                          e,
                          exc_info=True)

    def send_feedback(self, users):
        if not users:
            return
        sids = {'sid_list': [u['@sid'] for u in users]}
        data = gen_encrypt_json_context(
            ujson.dumps(sids),
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH)
        try:
            resp = get_from_remote(
                settings.STATS_VISITORS,
                settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                settings.PRIVATE_KEY_PATH,
                data=data,
                headers={'Content-Type': 'application/json'})
            data = xmltodict.parse(resp)
            r = data['visitors']['res']
            assert r == RESP_RESULT.S
        except Exception, e:
            logging.error('stats_visitors_feedback_err: %s',
                          e,
                          exc_info=True)



