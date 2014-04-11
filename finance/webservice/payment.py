import logging
import settings
import ujson

from common.error import ErrorCode
from common.error import UserError
from models.transaction import create_trans
from models.transaction import update_trans
from models.transaction import get_trans_by_id
from models.processor import get_processor
from webservice.base import BaseJsonResource
from webservice.base import BaseHtmlResource

from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.constant import SERVICES
from B2SRespUtils.generate import temp_content

class PaymentInitResource(BaseJsonResource):
    encrypt = True

    def _on_post(self, req, resp, conn, **kwargs):
        data = decrypt_json_resp(req.stream,
                                 settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                 settings.PRIVATE_KEY_PATH)
        data = ujson.loads(data)

        id_trans = create_trans(conn,
                                data['order'], data['user'],
                                data['invoices'], data['amount'],
                                data['invoicesData'])

        pm_cookie = {"id_user": data['user'],
                     "id_order": data['order'],
                     "amount_due": data['amount'],
                     "id_invoices": data['invoices'],
                     "internal_trans": id_trans}

        pm_cookie = ujson.dumps(pm_cookie)
        update_trans(conn,
                     {'cookie': pm_cookie},
                     where={'id': id_trans})

        pm_init = self.procession_options(conn)
        return {'pm_init': pm_init,
                'cookie': pm_cookie}

    def procession_options(self, conn):
        proc_list = get_processor(conn)
        data = {'obj_list': proc_list}
        return temp_content("processor.xml", **data)


class PaymentFormResource(BaseHtmlResource):
    template = "payment_form.html"
    encrypt = True
    service = SERVICES.USR

    def _on_post(self, req, resp, conn, **kwargs):
        data = decrypt_json_resp(req.stream,
                                 settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                                 settings.PRIVATE_KEY_PATH)
        data = ujson.loads(data)
        self.valid_check(conn, data)
        return self.payment_form(data['processor'],
                                 data['success'],
                                 data['failure'])

    def valid_check(self, conn, data):
        try:
            required_fields = ['cookie', 'processor', 'gateway', 'success',
                               'failure']
            for field in required_fields:
                assert field in data, "Miss %s in request" % field

            cookie = ujson.loads(data['cookie'])
            trans = get_trans_by_id(conn, cookie['internal_trans'])
            assert len(trans) == 1, "No trans for cookie %s" % cookie

            trans = trans[0]
            assert data['cookie'] == trans['cookie'], (
                "invalid cookie: %s expected: %s"
                % (cookie, trans['cookie']))
            return trans
        except AssertionError, e:
            logging.error("pm_form_invalid_request, param : %s "
                          "error: %s", data, e, exc_info=True)
            raise UserError(ErrorCode.PMF_INVALID_REQ[0],
                            ErrorCode.PMF_INVALID_REQ[1])

    def payment_form(self, id_processor, url_success, url_failure):
        # TODO: implementation
        return {'processor': id_processor,
                'success': url_success,
                'failure': url_failure}