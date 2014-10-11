import ujson
import logging
import settings

from datetime import datetime
from webservice.base import BaseXmlResource

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp


class SensorBaseResource(BaseXmlResource):
    encrypt = True

    login_required = {'get': False, 'post': False}
    date_format = "%Y-%m-%d"

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            data = decrypt_json_resp(
                req.stream,
                settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                settings.PRIVATE_KEY_PATH)
            params = ujson.loads(data)
            req._params.update(params)
        except Exception, e:
            logging.error("sensor_requeset_err: %s", str(e), exc_info=True)
            raise

    def _get_req_range(self, req):
        where = {}
        from_ = req.get_param('from')
        to = req.get_param('to')

        if from_:
            from_ = datetime.strptime(from_, self.date_format)
            where['visit_time__>='] = from_
        if to:
            to = datetime.strptime(to, self.date_format)
            where['visit_time__<='] = to

        return where
