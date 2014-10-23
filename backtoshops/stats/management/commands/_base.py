import ujson
import settings
import xmltodict

from datetime import datetime, timedelta
from optparse import make_option
from django.core.management.base import BaseCommand

from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote
from B2SCrypto.constant import SERVICES


class StatsCommand(BaseCommand):
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

    def _send_feedback(self, url, data):
        data = gen_encrypt_json_context(
            ujson.dumps(data),
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH)
        resp = get_from_remote(
            url,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH,
            data=data,
            headers={'Content-Type': 'application/json'})
        return xmltodict.parse(resp)
