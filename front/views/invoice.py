import settings

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SUtils.errors import ValidationError
from common.data_access import data_access
from views.base import BaseHtmlResource


class InvoiceResource(BaseHtmlResource):
    template = '_order_invoices.html'
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, **kwargs):
        order_id = kwargs.get('id_order')
        if not order_id:
            raise ValidationError('ERR_ID')

        remote_resp = data_access(REMOTE_API_NAME.GET_INVOICES, req, resp,
                                  order=order_id, brand=settings.BRAND_ID)
        return {'obj': remote_resp, 'order_id': order_id}
