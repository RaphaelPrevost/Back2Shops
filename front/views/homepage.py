from B2SFrontUtils.constants import REMOTE_API_NAME
from common.data_access import data_access
from common.utils import get_brief_product_list
from views.base import BaseHtmlResource

class HomepageResource(BaseHtmlResource):
    template = 'index.html'

    def _on_get(self, req, resp, **kwargs):
        all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
        return {'product_list': get_brief_product_list(all_sales)}


class MentionLegalResource(BaseHtmlResource):
    template = 'mention_legal.html'


class CGVResource(BaseHtmlResource):
    template = 'cgv.html'


class CommandsAndDeliveriesResource(BaseHtmlResource):
    template = 'commands_deliveries.html'
