import falcon
import logging
import settings
import ujson
import urllib
import urllib2

from datetime import datetime

from webservice.base import BaseHtmlResource
from webservice.base import BaseXmlResource
from webservice.base import BaseJsonResource
from webservice.base import BaseResource
from common.constants import PaymentStatus
from common.error import UserError
from common.error import ErrorCode
from common.utils import remote_payment_init
from common.utils import remote_payment_form
from models.invoice import get_invoice_by_order
from models.invoice import get_iv_numbers
from models.invoice import get_sum_amount_due
from models.paypal import create_trans_paypal
from models.transaction import create_trans
from models.transaction import get_trans_by_id
from models.transaction import update_trans
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
            logging.error("pm_init_err: %s", e, exc_info=True)
            return {'error': e.code}
        except Exception, e:
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


class PaymentFormResource(BaseHtmlResource):
    login_required = {'get': False, 'post': False}

    def _on_get(self, req, resp, conn, **kwargs):
        return self._on_post(req, resp, conn, **kwargs)

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
                      'url_success': url_success,
                      'url_failure': url_failure,
                      'update_time': datetime.now(),
                    }
            where = {'id': id_trans}
            update_trans(conn, values, where)

            pm_form = remote_payment_form(trans['cookie'],
                                          id_processor,
                                          id_trans)
            logging.info("payment_form_response: %s", pm_form)
            return pm_form
        except UserError, e:
            logging.error("pm_form_err: %s", e, exc_info=True)
            return {'error': e.code}
        except Exception, e:
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

class PaymentProcessResource(BaseResource):
    def _on_get(self, req, resp, conn, **kwargs):
        id_trans = kwargs['id_trans']
        trans = get_trans_by_id(conn, id_trans)[0]
        payment_status = req.get_param('payment_status')
        if payment_status.lower() == PaymentStatus.COMPLETED:
            url = trans['url_success']
        else:
            url = trans['url_failure']

        req._params.update(kwargs)
        create_trans_paypal(conn, req._params)
        query = urllib.urlencode(req._params)
        uri = '?'.join([url, query])

        self.redirect(uri)

class PaymentGatewayResource(BaseResource):
    def _on_post(self, req, resp, conn, **kwargs):
        r_verify = self.return_ipn_msg()
        logging.error(r_verify)

    def gen_resp(self, resp, data):
        resp.status = falcon.HTTP_202

    def return_ipn_msg(self):
        query_string = "cmd=_notify-validate&"
        query_string += self.request.query_string
        req = urllib2.Request(settings.PAYPAL_SERVER, data=query_string)
        resp = urllib2.urlopen(req)
        return resp.read()
