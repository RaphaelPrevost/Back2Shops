import falcon
import logging
import settings
import ujson
from pytz import timezone

from common.constants import CUR_CODE
from common.error import ErrorCode
from common.error import UserError
from common.utils import gen_hmac
from models.paybox import update_or_create_trans_paybox
from models.paypal import update_or_create_trans_paypal
from models.processor import get_processor
from models.transaction import create_trans
from models.transaction import get_trans_by_id
from models.transaction import update_trans
from webservice.base import BaseHtmlResource
from webservice.base import BaseJsonResource
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
            assert 'processor' in data, "Miss processor in request"
            if data['processor'] == '1':
                required_fields = ['cookie', 'url_notify', 'url_return',
                                   'url_cancel']
            elif data['processor'] == '4':
                required_fields = ['cookie', 'url_success', 'url_failure',
                                   'url_cancel', 'url_waiting', 'url_return']

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

    def _get_dt_with_timezone(self, dt):
        local_timezone = timezone(settings.B2S_TIMEZONE)
        return local_timezone.localize(dt)

    def _get_paybox_form_data(self, fields, trans, query):
        data = {
            'PBX_SITE': settings.PAYBOX_SITE,
            'PBX_RANG': settings.PAYBOX_RANG,
            'PBX_IDENTIFIANT': settings.PAYBOX_IDENTIFIANT,
            'PBX_TOTAL': int(trans['amount_due'] * 100),
            'PBX_DEVISE': CUR_CODE.toDict().get(trans['currency'], ''),
            'PBX_CMD': trans['id_order'],
            'PBX_PORTEUR': query['user_email'],
            'PBX_RETOUR': 'Mt:M;Ref:R;Auto:A;Erreur:E',
            'PBX_HASH': settings.PAYBOX_HASH_TYPE,
            'PBX_TIME': self._get_dt_with_timezone(trans['create_time']
                                                  ).isoformat(),
            'PBX_EFFECTUE': query['url_success'],
            'PBX_REFUSE': query['url_failure'],
            'PBX_ANNULE': query['url_cancel'],
            'PBX_ATTENTE': query['url_waiting'],
            'PBX_REPONDRE_A': query['url_return'],

            # for debug:
            # 'PBX_LANGUE': 'GBR',
            # 'PBX_ERRORCODETEST': '00004',
        }
        fields.remove('PBX_HMAC')
        message = '&'.join(map(lambda k: '%s=%s' % (k, data[k]), fields))
        data.update({'PBX_HMAC': gen_hmac(settings.PAYBOX_HMAC_KEY,
                                          message).upper()})
        return data

    def payment_form(self, query, trans):
        processor = query['processor']
        if int(processor) == 1:
            self.template = "paypal_form.html"
            url_return = query['url_return']
            url_cancel = query['url_cancel']
            url_notify = query['url_notify']
            return {'object': {
                'seller_email': settings.SELLER_EMAIL,
                'currency': trans['currency'],
                'iv_numbers': trans['iv_numbers'],
                'amount_due': trans['amount_due'],
                'url_return': url_return,
                'url_cancel': url_cancel,
                'url_notify': url_notify
                }}

        if int(processor) == 4:
            self.template = "paybox_form.html"
            fields = ['PBX_SITE', 'PBX_RANG', 'PBX_IDENTIFIANT', 'PBX_TOTAL',
                      'PBX_DEVISE', 'PBX_CMD', 'PBX_PORTEUR', 'PBX_RETOUR',
                      'PBX_HASH', 'PBX_TIME',
                      'PBX_EFFECTUE', 'PBX_REFUSE',
                      'PBX_ANNULE', 'PBX_ATTENTE', 'PBX_REPONDRE_A',

                      ## for debug:
                      # 'PBX_ERRORCODETEST',
                      # 'PBX_LANGUE',

                      # place PBX_HMAC at the end of form
                      'PBX_HMAC']
            return {'object': {
                'form_fields': fields,
                'form_data': self._get_paybox_form_data(fields[:], trans, query),
                'post_action': settings.PAYBOX_REQUEST_URL,
                'iv_numbers': trans['iv_numbers'],
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
            conn.rollback()
            logging.error('paypal_verified_err: %s', e, exc_info=True)
            resp.status = falcon.HTTP_500
        resp.status = falcon.HTTP_200


class PayboxTransResource(BaseResource):
    def _on_post(self, req, resp, conn, **kwargs):
        """
        1. Update transaction status to Paid for completed paybox transaction.
        2. Update or create paybox transaction.
        """
        try:
            req._params.update(kwargs)
            id_trans = req.get_param('id_trans')

            # TODO: check payment status
            # payment_status = req.get_param('payment_status')
            # if payment_status.lower() == TRANS_PAYPAL_STATUS.COMPLETED:
            #     update_trans(conn,
            #                  values={'status': TRANS_STATUS.TRANS_PAID},
            #                  where={'id': id_trans})
            update_or_create_trans_paybox(conn, req._params)
        except Exception, e:
            conn.rollback()
            logging.error('paybox_verified_err: %s', e, exc_info=True)
            resp.status = falcon.HTTP_500
        resp.status = falcon.HTTP_200