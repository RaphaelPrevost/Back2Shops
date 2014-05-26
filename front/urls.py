import re
import gevent
import settings

from views.homepage import HomepageResource
from views.login import LoginResource
from views.payment import PaypalSuccessResource
from views.payment import PaypalFailureResource
from views.payment import PaymentFormResource
from views.product import ProductInfoResource
from views.product import ProductListResource
from views.redirect import GenericRedirectResource
from views.register import RegisterResource
from views.user import UserResource
from webservice import crypto
from webservice import download
from webservice.aux import AuxResource

from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import send_reload_signal
from B2SFrontUtils.constants import REMOTE_API_NAME

# the url of these roles are configurable in BO
role_res_mapping = {
    FRT_ROUTE_ROLE.HOMEPAGE: HomepageResource,
    FRT_ROUTE_ROLE.LOGIN: LoginResource,
    FRT_ROUTE_ROLE.REGISTER: RegisterResource,
    FRT_ROUTE_ROLE.USER_INFO: UserResource,
    FRT_ROUTE_ROLE.PRDT_LIST: ProductListResource,
    FRT_ROUTE_ROLE.PRDT_INFO: ProductInfoResource,
}

# default url of roles
role_default_urlpatterns = {
    FRT_ROUTE_ROLE.HOMEPAGE: r'/',
    FRT_ROUTE_ROLE.LOGIN: r'/login',
    FRT_ROUTE_ROLE.REGISTER: r'/register',
    FRT_ROUTE_ROLE.USER_INFO: r'/user_info',
    FRT_ROUTE_ROLE.PRDT_LIST: r'/products',
    FRT_ROUTE_ROLE.PRDT_INFO: r'/products/{id_sale}',
}

# these urls are not configurable in BO
fixed_urlpatterns = {
    r'/paypal/{id_trans}/success': PaypalSuccessResource,
    r'/paypal/{id_trans}/failure': PaypalFailureResource,
    r'/webservice/1.0/pub/JSONAPI': AuxResource,
    r'/webservice/1.0/pub/apikey.pem': crypto.APIPubKey,

    # TODO: Remove, here just for payment test
    r'/payment/{id_trans}/form': PaymentFormResource,

    # static files
    r'/js/{name}': download.JsItem,
    r'/css/{name}': download.CssItem,
    r'/img/{name}': download.ImgItem,

    # access theme assets
    r'/templates/{theme}/{file_type}/{name}': download.AssetItem,
}


param_pattern = re.compile(r'\(\\p{L}\+\?\)')

class BrandRoutes(object):
    _instance = None
    routes_dict = {}  # id -> route
    role_mapping = {} # role -> route list

    def __new__(cls, *args, **kwargs):
        # singleton
        if not cls._instance:
            cls._instance = super(BrandRoutes,
                                  cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def refresh(self):
        resp_dict = data_access(REMOTE_API_NAME.GET_ROUTES)
        if not resp_dict: return

        routes = resp_dict['routes'].get('route') or []
        if isinstance(routes, dict):
            routes = [routes]

        role_mapping = {}
        for route in routes:
            role = route['template']
            if role not in role_mapping:
                role_mapping[role] = {}
            role_mapping[role][route['@id']] = route
        self.role_mapping = role_mapping
        self.routes_dict = dict([(route['@id'], route) for route in routes])

        if not settings.PRODUCTION:
            send_reload_signal()

    def url_res_mapping(self):
        urlpatterns = {}
        for url, res in fixed_urlpatterns.iteritems():
            urlpatterns[url] = res()

        if not self.routes_dict:
            if settings.PRODUCTION:
                self.refresh()
            else:
                gevent.spawn(self.refresh)

        if self.routes_dict:
            for route in self.routes_dict.itervalues():
                kwargs = {
                    'title': route['meta']['#text']
                             if route['meta']['@name'] == 'title' else '',
                    'desc': route.get('content', ''),
                }
                url = self._format_url(route)
                if route.get('redirect') and route['redirect'].get('@to'):
                    redirect_to, param_mapping = self._format_redirect_url(route)
                    kwargs.update({
                        'redirect_to': redirect_to,
                        'redirect_param_mapping': param_mapping,
                    })
                    urlpatterns[url] = GenericRedirectResource(**kwargs)
                else:
                    urlpatterns[url] = self._get_res(route['template'])(**kwargs)

            # add default url for missing role
            urlpatterns.update(
                dict([(url, self._get_res(role)())
                      for role, url in role_default_urlpatterns.iteritems()
                      if role not in self.role_mapping]))
        else:
            # add default url
            urlpatterns.update(
                dict([(url, self._get_res(role)())
                      for role, url in role_default_urlpatterns.iteritems()])
            )
        return urlpatterns

    def get_url_format(self, role):
        if self.role_mapping:
            route = self.role_mapping[role].values()[0]
            url_pattern = self._format_url(route, '%%(%s)s')
        else:
            url_pattern = re.sub(r'{(\w+)}', lambda m: '%%(%s)s' % m.groups(),
                                 role_default_urlpatterns[role])
        return url_pattern

    def _get_res(self, role):
        return role_res_mapping.get(role, HomepageResource)

    def _format_url(self, route, param_format='{%s}'):
        url_pattern = route.get('url') or ''
        params = self._get_sorted_params(route)
        for p in params:
            url_pattern = param_pattern.sub(param_format % p['#text'],
                                            url_pattern, count=1)
        return url_pattern

    def _get_sorted_params(self, route):
        params = route.get('param') or []
        if isinstance(params, dict):
            params = [params]
        params.sort(key=lambda x: int(x['@number']))
        return params

    def _format_redirect_url(self, route):
        redirect_to = route['redirect']['@to']
        if redirect_to in self.routes_dict:
            redirect_route = self.routes_dict[redirect_to]
            redirect_to = self._format_url(redirect_route, '%%(%s)s')
            redirect_params = [p['#text'] for p in
                                    self._get_sorted_params(redirect_route)]
            params = [p['#text'] for p in self._get_sorted_params(route)]
            param_mapping = dict(zip(params, redirect_params))
        else:
            redirect_to = '/'
            param_mapping = {}
        return redirect_to, param_mapping

