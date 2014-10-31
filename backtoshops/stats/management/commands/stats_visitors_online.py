import logging
import ujson
import settings

from stats.management.commands._base import StatsCommand
from B2SCrypto.utils import get_from_remote
from B2SCrypto.constant import SERVICES
from B2SUtils.redis_cli import redis_cli

VISITORS_ONLINE = "VISITORS_ONLINE"
class Command(StatsCommand):
    help = "Collect current visitors count information from user server"

    def handle(self, *args, **options):
        url = settings.STATS_VISITORS_ONLINE

        try:
            data = get_from_remote(
                url,
                settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                settings.PRIVATE_KEY_PATH)
            count = ujson.loads(data)['count']
            cli = redis_cli(settings.SALES_SIM_REDIS)
            cli.set(VISITORS_ONLINE, count)

        except Exception, e:
            logging.error('stats_visitors_online: %s',
                          e,
                          exc_info=True)
