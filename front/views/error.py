from common.m17n import gettext as _
from views.base import BaseHtmlResource

class GeneralErrorResource(BaseHtmlResource):
    template = "general_error_page.html"

    def _on_get(self, req, resp, **kwargs):
        err = _('Sorry, our server met problems. Please try later.')
        return {'err': err}
