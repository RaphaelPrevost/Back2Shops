import logging
import ujson

from webservice.base import BaseXmlResource
from common.error import UserError
from common.error import ErrorCode
from common.utils import remote_payment_init
from models.invoice import get_invoice_by_order
from models.invoice import get_sum_amount_due
from models.transaction import create_trans
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
            id_order, id_invoices, invoices = self.valid_check(conn,
                                                     id_order,
                                                     id_invoices)
            amount_due = get_sum_amount_due(conn, id_invoices)
            iv_data = self.get_unitary_invoice(invoices)

            resp = remote_payment_init(
                id_order, self.users_id,
                amount_due, id_invoices,
                iv_data)

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
