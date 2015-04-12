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


import gevent
import falcon
import httplib
import logging
import re
import settings
import ujson
import urllib
import urllib2
from datetime import datetime

from B2SProtocol.constants import PAYMENT_TYPES
from B2SProtocol.constants import TRANS_PAYPAL_STATUS
from B2SProtocol.constants import TRANS_STATUS
from B2SProtocol.constants import INVOICE_STATUS
from common.constants import PAYPAL_VERIFIED
from common.email_utils import send_order_email
from common.email_utils import send_order_email_to_service
from common.error import ErrorCode
from common.error import UserError
from common.utils import get_client_ip
from common.utils import remote_payment_form
from common.utils import remote_payment_init
from models.invoice import get_invoice_by_id
from models.invoice import get_invoice_by_order
from models.invoice import get_iv_numbers
from models.invoice import get_sum_amount_due
from models.invoice import update_invoice
from models.stats_log import log_incomes
from models.transaction import create_trans
from models.transaction import get_trans_by_id
from models.transaction import update_trans
from models.user import get_user_email
from webservice.base import BaseJsonResource
from webservice.base import BaseResource
from webservice.base import BaseXmlResource
from webservice.invoice import BaseInvoiceMixin


class PaymentInitResource(BaseXmlResource, BaseInvoiceMixin):
    login_required = {'get': False, 'post': True}

    def gen_resp(self, resp, data):
        payment_init = data.get('payment_init')
        if payment_init is not None:
            resp.body = payment_init
            resp.content_type = "application/xml"
        else:
            return super(PaymentInitResource, self).gen_resp(resp, data)

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            id_order = req.get_param('order')
            id_invoices = req.get_param('invoices')
            logging.info("payment_init_request: "
                         "id_order - %s, "
                         "id_invoices - %s", id_order, id_invoices)
            id_order, id_invoices, invoices = self.valid_check(conn,
                                                     id_order,
                                                     id_invoices)
            amount_due, currency = get_sum_amount_due(conn, id_invoices)

            iv_data = self.get_unitary_invoice(invoices)
            iv_numbers = get_iv_numbers(conn, id_invoices)

            resp = remote_payment_init(
                id_order, self.users_id,
                amount_due, currency, id_invoices,
                iv_numbers, iv_data)

            resp = ujson.loads(resp)
            pm_init = resp['pm_init']
            cookie = resp['cookie']

            trans_id = create_trans(conn, id_order, id_invoices,
                                    amount_due, cookie)

            trans_prop = '<payment transaction="%s"' % trans_id
            pm_init = pm_init.replace('<payment', trans_prop)

            return {'payment_init': pm_init}

        except UserError, e:
            conn.rollback()
            logging.error("pm_init_err: %s", e, exc_info=True)
            return {'error': e.code}
        except Exception, e:
            conn.rollback()
            logging.error("pm_init_err: %s", e, exc_info=True)
            return {'error': "SERVER ERROR"}

    def get_unitary_invoice(self, invoices):
        iv_content_list = []
        for invoice in invoices:
            iv_id = invoice['id']
            iv_xml = invoice['invoice_xml']
            content = self.parse_invoices_content(iv_xml)
            xml_update = '<invoice id="%s"' % iv_id
            content.replace("<invoice", xml_update)
            iv_content_list.append(content)
        iv_content = self.unitary_content(iv_content_list)
        return iv_content


    def valid_check(self, conn, id_order, id_invoices):
        try:
            assert id_order is not None, "Miss order in request"
            assert id_invoices is not None, "Miss invoices in request"
            id_invoices = ujson.loads(id_invoices)

            oi = get_invoice_by_order(conn, id_order)
            id_oi = [item['id'] for item in oi]

            ex_invoices = set(id_invoices) - set(id_oi)
            assert len(ex_invoices) == 0, ("invoices %s not belongs "
                                           "to order %s"
                                           % (ex_invoices, id_order))
        except (AssertionError, TypeError, ValueError), e:
            logging.error("pm_init_req_err: %s", e, exc_info=True)
            raise UserError(ErrorCode.PM_ERR_INVALID_REQ[0],
                            ErrorCode.PM_ERR_INVALID_REQ[1])
        return id_order, id_invoices, oi


class PaymentFormResource(BaseJsonResource):
    login_required = {'get': False, 'post': True}

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            id_trans = req.get_param('transaction')
            id_processor = req.get_param('processor')
            url_success = req.get_param('success')
            url_failure = req.get_param('failure')
            logging.info("payment_form_request: "
                         "id_trans - %s,"
                         "id_processor - %s,"
                         "url_success - %s,"
                         "url_failure - %s ",
                         id_trans, id_processor, url_success, url_failure)
            trans = self.valid_check(conn, id_trans, id_processor,
                                     url_success, url_failure)

            values = {'id_processor': id_processor,
                      'url_success': urllib.unquote(url_success),
                      'url_failure': urllib.unquote(url_failure),
                      'update_time': datetime.now(),
                    }
            where = {'id': id_trans}
            update_trans(conn, values, where)

            pm_form = remote_payment_form(
                trans['cookie'], id_processor, id_trans,
                user_email=get_user_email(conn, self.users_id),
                url_success=url_success,
                url_failure=url_failure)
            logging.info("payment_form_response: %s", pm_form)
            return {'form': pm_form}
        except UserError, e:
            conn.rollback()
            logging.error("pm_form_err: %s", e, exc_info=True)
            return {'error': e.code}
        except Exception, e:
            conn.rollback()
            logging.error("pm_form_err: %s", e, exc_info=True)
            return {'error': "SERVER ERROR"}

    def valid_check(self, conn, id_trans, id_processor, url_success, url_failure):
        try:
            assert id_trans is not None, "Miss transaction in request"
            assert id_processor is not None, "Miss processor in request"
            assert url_success is not None , "Miss success URL in request"
            assert url_failure is not None , "Miss failure URL in request"

            trans = get_trans_by_id(conn, id_trans)
            assert len(trans) == 1, "Transaction not exist"
            return trans[0]
        except AssertionError, e:
            logging.error("pm_form_req_err: %s", e, exc_info=True)
            raise UserError(ErrorCode.PM_ERR_INVALID_REQ[0],
                            ErrorCode.PM_ERR_INVALID_REQ[1])

class BasePaymentHandlerResource(BaseResource):
    id_trans = None
    payment_type = None

    def _valid_check(self, conn):
        raise NotImplementedError

    def _fin_handled_err_code(self):
        raise NotImplementedError

    def handle_completed(self, conn, trans):
        """
        1. Update invoice status to PAID and amount_paid value.
        2. Update transaction status to PAID.
        """
        try:

            id_invoices = ujson.loads(trans['id_invoices'])
            for id_iv in id_invoices:
                iv = get_invoice_by_id(conn, id_iv)
                if iv is None:
                    logging.error("critical_err: verified invoice "
                                  "not exist: %s", id_iv, exc_info=True)
                    continue
                values = {'amount_paid': iv['amount_due'],
                          'status': INVOICE_STATUS.INVOICE_PAID}
                update_invoice(conn, id_iv, values, iv=iv)
                log_incomes(conn, id_iv)

            update_trans(conn,
                         values={'status': TRANS_STATUS.TRANS_PAID},
                         where={'id': trans['id']})

        except UserError, e:
            logging.error("%s_verified_error: %s",
                          PAYMENT_TYPES.toReverseDict()[self.payment_type].lower(), e,
                          exc_info=True)
            raise

        try:
            send_order_email_to_service()
        except Exception, e:
            logging.error("Failed to send order email: %s", e, exc_info=True)
        try:
            send_order_email(conn, trans['id_order'])
        except Exception, e:
            logging.error("Failed to send order email: %s", e, exc_info=True)


    def fin_trans_notify(self, trans, data):
        cookie = ujson.loads(trans['cookie'])
        fin_internal_trans = cookie['internal_trans']
        url = settings.FIN_PAYMENT_NOTIFY_URL.get(self.payment_type) % {
            'id_trans': fin_internal_trans
        }
        if isinstance(data, (dict, list)):
            data = urllib.urlencode(data)
        req = urllib2.Request(url, data=data)
        resp = urllib2.urlopen(req)
        resp_code = resp.getcode()
        if resp_code != httplib.OK:
            logging.error('%s_trans_failure for %s got status: %s',
                          PAYMENT_TYPES.toReverseDict()[self.payment_type].lower(),
                          fin_internal_trans, resp_code)
            raise UserError(*self._fin_handled_err_code())


class BasePaypalHandlerResource(BasePaymentHandlerResource):
    payment_type = PAYMENT_TYPES.PAYPAL

    def _on_post(self, req, resp, conn, **kwargs):
        self.id_trans = kwargs['id_trans']

    def _fin_handled_err_code(self):
        return ErrorCode.PP_FIN_HANDLED_ERR

    def _valid_check(self, conn):
        if self.request.get_param('receiver_email') != settings.SELLER_EMAIL:
            logging.error('paypal_valid_err: wrong receiver email %s',
                          self.request.query_string,
                          exc_info=True)
            raise UserError(ErrorCode.PP_ERR_RECEIVER_EMAIL[0],
                            ErrorCode.PP_ERR_RECEIVER_EMAIL[1])

        trans = get_trans_by_id(conn, self.id_trans)
        if len(trans) == 0:
            logging.error('paypal_valid_err: trans(%s) not exist %s',
                          self.id_trans, self.request.query_string,
                          exc_info=True)
            raise UserError(ErrorCode.PP_ERR_NO_TRANS[0],
                            ErrorCode.PP_ERR_NO_TRANS[1])

        trans = trans[0]
        amount_due = float(trans['amount_due'])
        mc_gross = float(self.request.get_param('mc_gross'))
        if amount_due != mc_gross:
            logging.error('paypal_valid_err: mc_gross %s is not same '
                          'as expected amount due: %s for request: %s',
                          mc_gross, amount_due, self.request.query_string,
                          exc_info=True)
            raise UserError(ErrorCode.PP_ERR_MC_GROSS[0],
                            ErrorCode.PP_ERR_MC_GROSS[1])

        return trans


class PaypalProcessResource(BasePaypalHandlerResource):
    def _on_post(self, req, resp, conn, **kwargs):
        """
        1. valid check.
        2. Handle complete paypal transaction.
        3. notify finance server for paypal transaction.
        4. redirect to front success/failure page.
        """
        super(PaypalProcessResource, self)._on_post(req, resp, conn, **kwargs)

        try:
            trans = self._valid_check(conn)
            req._params.update(kwargs)

            payment_status = req.get_param('payment_status')
            if payment_status.lower() == TRANS_PAYPAL_STATUS.COMPLETED:
                url = trans['url_success']
                gevent.spawn(self.handle_completed, conn, trans)
            else:
                url = trans['url_failure']

            self.fin_trans_notify(trans, self.request.query_string)

            query = urllib.urlencode(req._params)
            uri = '?'.join([url, query])
            self.redirect(uri)
        except UserError, e:
            conn.rollback()
            logging.error("paypal_process_err: %s", e, exc_info=True)
            url = settings.FRONT_PAYMENT_FAILURE % {'id_trans': self.id_trans}
            query = urllib.urlencode({'error': e.code})
            uri = '?'.join([url, query])
            self.redirect(uri)


class PaypalGatewayResource(BasePaypalHandlerResource):
    id_trans = None
    def _on_post(self, req, resp, conn, **kwargs):
        super(PaypalGatewayResource, self)._on_post(req, resp, conn, **kwargs)
        self.confirm_ipn_msg(conn)

    def gen_resp(self, resp, data):
        resp.status = falcon.HTTP_200

    def confirm_ipn_msg(self, conn):
        """
         1. Post complete, unaltered message backto to Paypal.
         2. Handle completed paypal transaction if get 'Verified' result.
         3. Notify finance server for paypal transaction.
        """
        trans = self._valid_check(conn)

        cmd = "cmd=_notify-validate&"
        query_string = cmd + self.request.query_string
        req = urllib2.Request(settings.PAYPAL_SERVER, data=query_string)
        resp = urllib2.urlopen(req)
        confirm_r = resp.read()
        if confirm_r == PAYPAL_VERIFIED:
            self.handle_completed(conn, trans)
        else:
            logging.error('invalid_paypal_ipn: %s - %s', confirm_r, query_string)

        gevent.spawn(self.fin_paypal_trans_notify, trans)

        return confirm_r


class BasePayboxHandlerResource(BasePaymentHandlerResource):
    payment_type = PAYMENT_TYPES.PAYBOX

    def _on_get(self, req, resp, conn, **kwargs):
        self.id_trans = kwargs['id_trans']

    def _fin_handled_err_code(self):
        return ErrorCode.PB_FIN_HANDLED_ERR

    def _valid_check(self, conn):
        resp_code = self.request.get_param('RespCode')
        amount = float(self.request.get_param('Amt')) / 100
        order_id = self.request.get_param('Ref')
        auth = self.request.get_param('Auth')

        # for a rejected transaction, this parameter is not sent back.
        if not auth:
            logging.error('paybox_valid_err: rejected transaction for '
                          'request %s',
                          self.request.query_string,
                          exc_info=True)
            raise UserError(ErrorCode.PB_ERR_REJECTED_TRANS[0],
                            ErrorCode.PB_ERR_REJECTED_TRANS[1])

        # authorization number is alphanumeric.
        if not re.match(r'^[a-zA-Z0-9]+$', auth):
            logging.error('paybox_valid_err: wrong authorization number %s for'
                          ' request %s',
                          auth, self.request.query_string,
                          exc_info=True)
            raise UserError(ErrorCode.PB_ERR_WRONG_AUTH[0],
                            ErrorCode.PB_ERR_WRONG_AUTH[1])

        # TODO: check ip address
        ip_addr = get_client_ip(self.request)
        logging.info('Paybox IPN request address %s for request %s',
                     ip_addr, self.request.query_string)

        trans = get_trans_by_id(conn, self.id_trans)
        if len(trans) == 0:
            logging.error('paybox_valid_err: trans(%s) not exist %s',
                          self.id_trans, self.request.query_string,
                          exc_info=True)
            raise UserError(ErrorCode.PB_ERR_NO_TRANS[0],
                            ErrorCode.PB_ERR_NO_TRANS[1])

        trans = trans[0]
        amount_due = float(trans['amount_due'])
        if amount_due != amount:
            logging.error('paybox_valid_err: paybox amount %s is not same '
                          'as expected amount due: %s for request: %s',
                          amount, amount_due, self.request.query_string,
                          exc_info=True)
            raise UserError(ErrorCode.PB_ERR_WRONG_AMOUNT[0],
                            ErrorCode.PB_ERR_WRONG_AMOUNT[1])

        if int(order_id) != int(trans['id_order']):
            logging.error('paybox_valid_err: order_id %s is not same as '
                          'expected order_id %s for request: %s',
                          order_id, trans['id_order'],
                          self.request.query_string,
                          exc_info=True)
            raise UserError(ErrorCode.PB_ERR_WRONG_ORDER[0],
                            ErrorCode.PB_ERR_WRONG_ORDER[1])
        return trans


class PayboxGatewayResource(BasePayboxHandlerResource):
    id_trans = None

    def _on_get(self, req, resp, conn, **kwargs):
        super(PayboxGatewayResource, self)._on_get(req, resp, conn, **kwargs)
        self.confirm_ipn_msg(conn)

    def confirm_ipn_msg(self, conn):
        """
         1. Post complete, unaltered message backto to Paybox.
         2. Handle completed paybox transaction if get '00000' resp_code.
         3. Notify finance server for paybox transaction.
        """
        trans = self._valid_check(conn)
        resp_code = self.request.get_param('RespCode')
        # TODO: put resp_code in B2SProtocol
        if resp_code == '00000':
            self.handle_completed(conn, trans)

        data = self.request._params
        data.update({
            'user_id': ujson.loads(trans['cookie']).get('id_user'),
            # TODO: add currency to users:transactions table
            'currency': 'EUR',
        })
        gevent.spawn(self.fin_trans_notify, trans, data)
        return resp_code

    def gen_resp(self, resp, data):
        resp.status = falcon.HTTP_200


class StripeProcessResource(BasePaymentHandlerResource):
    id_trans = None
    payment_type = PAYMENT_TYPES.STRIPE

    def _on_post(self, req, resp, conn, **kwargs):
        """
        1. valid check
        2. charge via finance server
        3. handle complete stripe transaction.
        4. notify finance server for stripe transaction.
        5. redirect to front success/failure page.
        """
        super(StripeProcessResource, self)._on_post(req, resp, conn, **kwargs)
        self.id_trans = kwargs['id_trans']
        url_success = req.get_param('url_success')
        url_failure = req.get_param('url_failure')
        try:
            trans = self._valid_check(conn)
            charge_req = urllib2.Request(
                    settings.FIN_PAYMENT_STRIPE_CHARGE_URL % {'id_trans': self.id_trans},
                    data=urllib.urlencode(req._params))
            charge_resp = urllib2.urlopen(charge_req).read()
            data = ujson.loads(charge_resp).get('resp_data') or {}
            if data.get('status') == 'succeeded':
                self.handle_completed(conn, trans)
                redirect_url = url_success
            else:
                redirect_url = url_failure
                query = urllib.urlencode({'error': data['error'].get('message') or ''})
                redirect_url = '?'.join([redirect_url, query])

                if data['error'].get('decline_code') == 'fraudulent':
                    logging.error('fraud payment: trans(id=%s), cookie%s',
                                  self.id_trans, trans['cookie'])

            gevent.spawn(self.fin_trans_notify, trans, charge_resp)
            self.redirect(redirect_url % {'id_trans': self.id_trans})

        except UserError, e:
            conn.rollback()
            logging.error("stripe_process_err: %s", e, exc_info=True)
            url = url_failure % {'id_trans': self.id_trans}
            query = urllib.urlencode({'error': e.code})
            uri = '?'.join([url, query])
            self.redirect(uri)

    def _valid_check(self, conn):
        trans = get_trans_by_id(conn, self.id_trans)
        if len(trans) == 0:
            logging.error('stripe_valid_err: trans(%s) not exist %s',
                          self.id_trans, self.request.query_string,
                          exc_info=True)
            raise UserError(ErrorCode.PM_ERR_INVALID_REQ[0],
                            ErrorCode.PM_ERR_INVALID_REQ[1])
        return trans[0]

