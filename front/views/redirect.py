import falcon
from views.base import BaseHtmlResource

class GenericRedirectResource(BaseHtmlResource):

    def __init__(self, **kwargs):
        super(GenericRedirectResource, self).__init__(**kwargs)
        self.redirect_to = kwargs.get('redirect_to') or '/'
        self.redirect_param_mapping = kwargs.get('redirect_param_mapping') or {}

    def _on_get(self, req, resp, **kwargs):
        params = {}
        for name, to_name in self.redirect_param_mapping.iteritems():
            params[to_name] = kwargs.get(name) or ''
        return self.redirect(self.redirect_to % params, code=falcon.HTTP_301)

    def _on_post(self, req, resp, **kwargs):
        raise NotImplemented
