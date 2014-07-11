import settings
import ujson
import urllib
import urllib2
import xmltodict

from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import get_url_format
from views.base import BaseHtmlResource
from B2SUtils.base_actor import as_list
from B2SFrontUtils.constants import REMOTE_API_NAME

def get_payment_url(id_order, id_invoices):
    url = get_url_format(FRT_ROUTE_ROLE.PAYMENT)
    url += "?%s" % urllib.urlencode({
        'id_order': id_order,
        'id_invoices': ujson.dumps(id_invoices)
    })
    return url


class PaymentResource(BaseHtmlResource):
    template = "payment.html"
    show_products_menu = False
    login_required = {'get': True, 'post': True}

    def _on_get(self, req, resp, **kwargs):
        id_order = req.get_param('id_order')
        id_invoices = req.get_param('id_invoices')
        remote_resp = data_access(REMOTE_API_NAME.INIT_PAYMENT, req, resp,
                               order=id_order,
                               invoices=id_invoices)
        err = (remote_resp.get('error') or remote_resp.get('err')) \
              if isinstance(remote_resp, dict) else ""
        if err:
            id_trans = ""
            processors = []
        else:
            payment = xmltodict.parse(remote_resp)
            err = payment.get('error', {}).get('#text')
            if err:
                err = "Error Message: %s" % err
            processors = as_list(payment.get('payment', {}).get('processor'))
            id_trans = payment.get('payment', {}).get('@transaction')

        return {'step': 'init',
                'err': err,
                'id_trans': id_trans,
                'processors': processors}

    def _on_post(self, req, resp, **kwargs):
        id_trans = req.get_param('id_trans')
        processor = req.get_param('processor')
        if processor == '1':
            trans = {'id_trans': id_trans}
            success_url = settings.PP_SUCCESS % trans
            failure_url = settings.PP_FAILURE % trans
            query = {'transaction': id_trans,
                     'processor': processor,
                     'success': success_url,
                     'failure': failure_url}
            form_resp = data_access(REMOTE_API_NAME.PAYMENT_FORM, req, resp,
                                    **query)
        else:
            form_resp = '<div class="errwrapper">NOT_SUPPORTED</div>'
        return {'step': 'form',
                'form': form_resp}


class PaypalSuccessResource(BaseHtmlResource):
    template = "paypal_success.html"

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}


class PaypalFailureResource(BaseHtmlResource):
    template = "paypal_failure.html"

    def _on_get(self, req, resp, **kwargs):
        params = req._params
        params.update({'id_trans': kwargs['id_trans']})
        return {'result': params}


