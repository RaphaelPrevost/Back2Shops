from common.m17n import trans_func
from views.base import BaseHtmlResource

class GeneralErrorResource(BaseHtmlResource):
    template = "general_error_page.html"

    def _on_get(self, req, resp, **kwargs):
        err = req.get_param('err') or 'INTERNAL_SERVER_ERROR'
        err = trans_func(err)
        return {'err': err}
