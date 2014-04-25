from common.data_access import data_access
from views.base import BaseHtmlResource
from B2SUtils.errors import ValidationError
from B2SFrontUtils.constants import REMOTE_API_NAME


class ProductListResource(BaseHtmlResource):
    template = "product_list.html"

    def _on_get(self, req, resp, **kwargs):
        remote_resp = data_access(REMOTE_API_NAME.GET_SALES,
                                  req, resp, **req._params)
        return {'products': remote_resp}


class ProductInfoResource(BaseHtmlResource):
    template = "product_info.html"

    def _on_get(self, req, resp, **kwargs):
        obj_id = req.get_param('id')
        if not obj_id:
            raise ValidationError('ERR_ID')

        remote_resp = data_access(REMOTE_API_NAME.GET_SALES,
                                  req, resp,
                                  obj_id=obj_id)
        return {'products': remote_resp}
