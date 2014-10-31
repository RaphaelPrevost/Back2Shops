from common.redis_utils import get_redis_cli
from webservice.base import BaseJsonResource


class SensorVisitorsOnlineResource(BaseJsonResource):
    encrypt = True

    def _on_get(self, req, resp, conn, **kwargs):
        cli = get_redis_cli()
        rst = cli.keys('SID:*')
        return {'count': len(rst)}
