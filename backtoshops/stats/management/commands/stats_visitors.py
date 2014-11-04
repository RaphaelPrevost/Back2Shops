import logging
import urllib
import settings
import xmltodict

from stats.models import Visitors
from stats.management.commands._base import StatsCommand
from B2SCrypto.utils import get_from_remote
from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import RESP_RESULT


class Command(StatsCommand):
    help = "Collect visitors statistics information from user server"

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
                try:
                    v = Visitors.objects.get(sid=user['@sid'])
                    v.sid = user['@sid']
                    v.visit_time = user['visit_time']
                    v.users_id = user['users_id']
                    v.save()
                except Visitors.DoesNotExist:
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
        try:
            data = self._send_feedback(settings.STATS_VISITORS, sids)
            r = data['visitors']['res']
            assert r == RESP_RESULT.S
        except Exception, e:
            logging.error('stats_visitors_feedback_err: %s',
                          e,
                          exc_info=True)



