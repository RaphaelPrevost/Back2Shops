import falcon
import logging
import settings
import ujson

from common.error import ErrorCode
from common.error import UserError
from models.transaction import create_trans
from models.transaction import update_trans
from models.transaction import get_trans_by_id
from models.paypal import update_or_create_trans_paypal
from models.processor import get_processor
from webservice.base import BaseJsonResource
from webservice.base import BaseHtmlResource
from webservice.base import BaseResource

from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import TRANS_PAYPAL_STATUS
from B2SProtocol.constants import TRANS_STATUS
from B2SRespUtils.generate import temp_content

class PaymentInitResource(BaseJsonResource):
    encrypt = True

    def _on_post(self, req, resp, conn, **kwargs):
        data = decrypt_json_resp(req.stream,
                                 settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                 settings.PRIVATE_KEY_PATH)
        logging.info("payment_init_request: %s", data)
        data = ujson.loads(data)

        id_trans = create_trans(conn,
                                data['order'],
                                data['user'],
                                data['invoices'],
                                data['invoices_num'],
                                data['amount'],
                                data['currency'],
                                data['invoicesData'])

        pm_cookie = {"id_user": long(data['user']),
                     "id_order": long(data['order']),
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
    template = ""
    encrypt = True
    service = SERVICES.USR

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            data = decrypt_json_resp(req.stream,
                                     settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                                     settings.PRIVATE_KEY_PATH)
            logging.info("payment_form_request: %s", data)
            query = ujson.loads(data)
            trans = self.valid_check(conn, query)
            return self.payment_form(query, trans)
        except Exception, e:
            logging.error('payment_form_err: %s', e, exc_info=True)
            raise

    def valid_check(self, conn, data):
        try:
            required_fields = ['cookie', 'processor', 'url_notify',
                               'url_return', 'url_cancel']
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

    def payment_form(self, query, trans):
        processor = query['processor']
        url_return = query['url_return']
        url_cancel = query['url_cancel']
        url_notify = query['url_notify']

        if int(processor) == 1:
            self.template = "paypal_form.html"

        return {'object': {
            'seller_email': settings.SELLER_EMAIL,
            'currency': trans['currency'],
            'iv_numbers': trans['iv_numbers'],
            'amount_due': trans['amount_due'],
            'url_return': url_return,
            'url_cancel': url_cancel,
            'url_notify': url_notify
            }}

class PaypalTransResource(BaseResource):
    def _on_post(self, req, resp, conn, **kwargs):
        """
        1. Update transaction status to Paid for completed paypal transaction.
        2. Update or create paypal transaction.
        """
        try:
            req._params.update(kwargs)
            id_trans = req.get_param('id_trans')

            payment_status = req.get_param('payment_status')
            if payment_status.lower() == TRANS_PAYPAL_STATUS.COMPLETED:
                update_trans(conn,
                             values={'status': TRANS_STATUS.TRANS_PAID},
                             where={'id': id_trans})
            update_or_create_trans_paypal(conn, req._params)
        except Exception, e:
            logging.error('paypal_verified_err: %s', e, exc_info=True)
            resp.status = falcon.HTTP_500
        resp.status = falcon.HTTP_200
