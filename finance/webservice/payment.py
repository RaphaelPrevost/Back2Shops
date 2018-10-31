# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


import falcon
import logging
import settings
import ujson
from pytz import timezone
import stripe

from common.constants import CUR_CODE
from common.error import ErrorCode
from common.error import ThirdPartyError
from common.error import UserError
from common.third_party.paybox import Paybox
from common.utils import gen_hmac
from models.paybox import update_or_create_trans_paybox
from models.paypal import update_or_create_trans_paypal
from models.stripe import update_or_create_trans_stripe
from models.processor import get_processor
from models.transaction import create_trans
from models.transaction import get_trans_by_id
from models.transaction import update_trans
from webservice.base import BaseHtmlResource
from webservice.base import BaseJsonResource
from webservice.base import BaseResource
from webservice.creditcard import CCAddResource

from B2SUtils import db_utils
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.constant import SERVICES
from B2SProtocol.constants import PAYMENT_TYPES
from B2SProtocol.constants import RESP_RESULT
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
            proc = int(data['processor'])
            if proc == PAYMENT_TYPES.PAYPAL:
                required_fields = ['cookie', 'url_notify', 'url_return',
                                   'url_cancel']
            elif proc == PAYMENT_TYPES.PAYBOX:
                required_fields = ['cookie', 'url_success', 'url_failure',
                                   'url_cancel', 'url_waiting', 'url_return']
            elif proc == PAYMENT_TYPES.STRIPE:
                required_fields = ['cookie', 'url_success', 'url_failure']

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
            'PBX_RETOUR': 'Amt:M;Ref:R;Auth:A;RespCode:E;CardType:C;PBRef:S',
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
        processor = int(query['processor'])
        if processor == PAYMENT_TYPES.PAYPAL:
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

        if processor == PAYMENT_TYPES.PAYBOX:
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

        if processor == PAYMENT_TYPES.STRIPE:
            self.template = "stripe_form.html"
            return {'object': {
                'api_key': settings.STRIPE_PUBLISH_API_KEY,
                'post_action': query['url_process'],
                'url_success': query['url_success'],
                'url_failure': query['url_failure'],
                'amount_due': int(trans['amount_due'] * 100),
                'name': 'Payment',
                'desc': '',
                'img': '',
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
            else:
                update_trans(conn,
                             values={'status': TRANS_STATUS.TRANS_FAIL},
                             where={'id': id_trans})
            update_or_create_trans_paypal(conn, req._params)
            resp.status = falcon.HTTP_200
        except Exception, e:
            #conn.rollback()
            logging.error('paypal_verified_err: %s', e, exc_info=True)
            resp.status = falcon.HTTP_500


class PayboxTransResource(BaseResource):
    def _on_post(self, req, resp, conn, **kwargs):
        """
        1. Update transaction status to Paid for completed paybox transaction.
        2. Update or create paybox transaction.
        """
        try:
            req._params.update(kwargs)
            id_trans = req.get_param('id_trans')

            # TODO: put resp code into constants
            resp_code = req.get_param('RespCode')
            if resp_code == '00000':
                update_trans(conn,
                             values={'status': TRANS_STATUS.TRANS_PAID},
                             where={'id': id_trans})
            else:
                update_trans(conn,
                             values={'status': TRANS_STATUS.TRANS_FAIL},
                             where={'id': id_trans})

            update_or_create_trans_paybox(conn, req._params)
            resp.status = falcon.HTTP_200
        except Exception, e:
            #conn.rollback()
            logging.error('paybox_verified_err: %s', e, exc_info=True)
            resp.status = falcon.HTTP_500


class StripeChargeResource(BaseJsonResource):
    def _on_post(self, req, resp, conn, **kwargs):
        try:
            req._params.update(kwargs)
            id_trans = req.get_param('id_trans')
            card_token = req.get_param('stripeToken')
            data = self.charge(conn, id_trans, card_token)
            logging.debug('trans(id=%s) stripe_charge_resp: %s',
                          id_trans, data)
            return {
                'resp_code': falcon.HTTP_200,
                'resp_data': data,
            }
        except stripe.error.StripeError, e:
            body = e.json_body
            data = body['error']
            #conn.rollback()
            logging.error('trans(id=%s) stripe_charge_err: %s',
                          id_trans, data, exc_info=True)

        except Exception, e:
            #conn.rollback()
            data = {'message': str(e)}
            logging.error('trans(id=%s) stripe_charge_err: %s',
                          id_trans, e, exc_info=True)

        return {
            'resp_code': falcon.HTTP_500,
            'resp_data': {'error': data},
        }

    def charge(self, conn, id_trans, card_token):
        trans = db_utils.select(conn, "transactions",
                       columns=['amount_due', 'currency', 'iv_numbers'],
                       where={'id': id_trans})[0]
        stripe.api_key = settings.STRIPE_SECRET_API_KEY
        resp = stripe.Charge.create(
            amount=int(trans[0] * 100),
            currency=trans[1],
            source=card_token,
            description="Charge for invoice num: %s" % trans[2],
        )
        return resp


class StripeTransResource(BaseResource):
    def _on_post(self, req, resp, conn, **kwargs):
        """
        1. Update transaction status to Paid for completed stripe transaction.
        2. Update or create stripe transaction.
        """
        try:
            id_trans = kwargs.get('id_trans')
            data = ujson.loads(req.query_string).get('resp_data') or {}

            if data.get('status') == 'succeeded':
                update_trans(conn,
                             values={'status': TRANS_STATUS.TRANS_PAID},
                             where={'id': id_trans})
            else:
                update_trans(conn,
                             values={'status': TRANS_STATUS.TRANS_FAIL},
                             where={'id': id_trans})

            if 'id' in data:
                update_or_create_trans_stripe(conn, id_trans, data)
            resp.status = falcon.HTTP_200

        except Exception, e:
            #conn.rollback()
            logging.error('stripe_trans_err: %s', e, exc_info=True)
            resp.status = falcon.HTTP_500


class PaymentAjaxResource(BaseJsonResource):
    encrypt = True
    service = SERVICES.USR

    def valid_check(self, conn, req, **kwargs):
        data = decrypt_json_resp(req.stream,
                                 settings.SERVER_APIKEY_URI_MAP[self.service],
                                 settings.PRIVATE_KEY_PATH)
        logging.info("payment_ajax_request: %s", data)
        data = ujson.loads(data)

        try:
            cookie = ujson.loads(data['cookie'])
            trans = get_trans_by_id(conn, cookie['internal_trans'])
            assert len(trans) == 1, "No trans for cookie %s" % cookie
            trans = trans[0]
            assert data['cookie'] == trans['cookie'], (
                "invalid cookie: %s expected: %s"
                % (cookie, trans['cookie']))

            id_card = CCAddResource().add_card(conn, {
                'id_user': trans['id_user'],
                'pan': data.get('pan'),
                'cvc': data.get('cvc'),
                'expiration_date': data.get('expiration_date'),
                'repeat': data.get('repeat'),
            })
            card = db_utils.select(conn, 'credit_card',
                                   where={'id': id_card, 'valid': True})[0]
            return trans, card

        except AssertionError, e:
            logging.error("pm_ajax_invalid_request, param : %s "
                          "error: %s", data, e, exc_info=True)
            raise UserError(ErrorCode.PMA_INVALID_REQ[0],
                            ErrorCode.PMA_INVALID_REQ[1])

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            trans, card = self.valid_check(conn, req, **kwargs)
        except ThirdPartyError, e:
            return {"res": RESP_RESULT.F, "err": e.desc}
        
        try:
            resp_data = Paybox().one_click_pay(
                trans['id'], trans['id_user'], trans['id_order'],
                card['paybox_token'], card['expiration_date'],
                trans['amount_due'], trans['currency'],
                repeat=card['repeat'])

            if resp_data['CODEREPONSE'] == '00000':
                update_trans(conn,
                             values={'status': TRANS_STATUS.TRANS_PAID},
                             where={'id': trans['id']})
            else:
                update_trans(conn,
                             values={'status': TRANS_STATUS.TRANS_FAIL},
                             where={'id': trans['id']})

            data = {
                'id_trans': trans['id'],
                'user_id': trans['id_user'],
                'currency': trans['currency'],
                'Amt': trans['amount_due'],
                'PBRef': resp_data['NUMTRANS'],
                'Auth': resp_data['AUTORISATION'],
                'RespCode': resp_data['CODEREPONSE'],
                'content': resp_data,
            }
            update_or_create_trans_paybox(conn, data)
            return {"res": RESP_RESULT.S, "err": ""}

        except ThirdPartyError, e:
            update_trans(conn,
                         values={'status': TRANS_STATUS.TRANS_FAIL},
                         where={'id': trans['id']})
            return {"res": RESP_RESULT.F, "err": e.desc}

        except Exception, e:
            #conn.rollback()
            logging.error('paybox_ajax_err: %s', e, exc_info=True)
            return {"res": RESP_RESULT.F, "err": str(e)}


class PaymentAutoResource(PaymentAjaxResource):

    def valid_check(self, conn, req, **kwargs):
        req._params.update(kwargs)
        logging.info("payment_auto_request: %s", req._params)

        try:
            cookie = req.get_param('cookie')
            cookie = ujson.loads(cookie)
            trans = get_trans_by_id(conn, cookie['internal_trans'])
            assert len(trans) == 1, "No trans for cookie %s" % cookie
            trans = trans[0]
            assert req.get_param('cookie') == trans['cookie'], (
                "invalid cookie: %s expected: %s"
                % (cookie, trans['cookie']))

            id_card = req.get_param('id_card')
            card = db_utils.select(conn, 'credit_card',
                                   where={'id': id_card, 'valid': True})
            assert len(card) == 1, "No valid card %s" % id_card

            return trans[0], card[0]

        except AssertionError, e:
            logging.error("pm_ajax_invalid_request, param : %s "
                          "error: %s", data, e, exc_info=True)
            raise UserError(ErrorCode.PM_AUTO_INVALID_REQ[0],
                            ErrorCode.PM_AUTO_INVALID_REQ[1])