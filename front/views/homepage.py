from B2SFrontUtils.constants import REMOTE_API_NAME
from common.data_access import data_access
from common.utils import get_brief_product_list
from views.base import BaseHtmlResource

class HomepageResource(BaseHtmlResource):
    template = 'index.html'

    def _on_get(self, req, resp, **kwargs):
        sales = data_access(REMOTE_API_NAME.GET_SALES,
                            req, resp, **req._params)
        return {'product_list': get_brief_product_list(sales)}

class EShopResource(BaseHtmlResource):
    template = 'eshop.html'
    cur_tab_index = 0

class LookbookResource(BaseHtmlResource):
    template = 'lookbook.html'
    cur_tab_index = 1


class MentionLegalResource(BaseHtmlResource):
    template = 'mention_legal.html'
    show_products_menu = False

class CGVResource(BaseHtmlResource):
    template = 'cgv.html'
    show_products_menu = False

class CommandsAndDeliveriesResource(BaseHtmlResource):
    template = 'commands_deliveries.html'
    show_products_menu = False
