from common.utils import get_from_sale_server
from webservice.base import BaseJsonResource

class SuggestResource(BaseJsonResource):
    login_required = {'get': False, 'post': False}

    def _on_get(self, req, resp, conn, **kwargs):
        like = req.get_param('like')
        query = {'like': like}
        suggests = get_from_sale_server('private/suggest', **query)
        return suggests
