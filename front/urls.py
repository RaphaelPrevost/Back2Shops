# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


import settings
import re

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SUtils.base_actor import as_list
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from views import error
from views import email
from views import homepage
from views import vessel
from views.basket import BasketAPIResource
from views.basket import BasketResource
from views.homepage import HomepageResource
from views.homepage import EShopResource
from views.homepage import LookbookResource
from views.invoice import InvoiceResource
from views.order import OrderAPIResource
from views.order import OrderAddressResource
from views.order import OrderAuthResource
from views.order import OrderInfoResource
from views.order import OrderListResource
from views.order import OrderUserResource
from views.order import ShippingAPIResource
from views.payment import PayboxCancelResource
from views.payment import PayboxFailureResource
from views.payment import PayboxSuccessResource
from views.payment import PayboxWaitingResource
from views.payment import PaymentResource
from views.payment import PaypalCancelResource
from views.payment import PaypalFailureResource
from views.payment import PaypalSuccessResource
from views.product import ProductInfoResource
from views.product import ProductListResource
from views.product import TypeListResource
from views.redirect import GenericRedirectResource
from views.reset_password import ResetPwdResource
from views.reset_password import ResetPwdRequestResource
from views.user import LoginAPIResource
from views.user import MyAccountResource
from views.user import RegisterAPIResource
from views.user import UserAPIResource
from views.user import UserAuthResource
from views.user import UserLogoutResource
from views.user import UserResource
from webservice import crypto
from webservice import download
from webservice.aux import AuxResource


# the url of these roles are configurable in BO
role_res_mapping = {
    FRT_ROUTE_ROLE.HOMEPAGE: HomepageResource,
    FRT_ROUTE_ROLE.USER_AUTH: UserAuthResource,
    FRT_ROUTE_ROLE.USER_LOGOUT: UserLogoutResource,
    FRT_ROUTE_ROLE.USER_INFO: UserResource,
    FRT_ROUTE_ROLE.MY_ACCOUNT: MyAccountResource,
    FRT_ROUTE_ROLE.RESET_PWD_REQ: ResetPwdRequestResource,
    FRT_ROUTE_ROLE.RESET_PWD: ResetPwdResource,
    FRT_ROUTE_ROLE.PRDT_LIST: ProductListResource,
    FRT_ROUTE_ROLE.PRDT_INFO: ProductInfoResource,
    FRT_ROUTE_ROLE.TYPE_LIST: TypeListResource,
    FRT_ROUTE_ROLE.BASKET: BasketResource,
    FRT_ROUTE_ROLE.ORDER_LIST: OrderListResource,
    FRT_ROUTE_ROLE.ORDER_INFO: OrderInfoResource,
    FRT_ROUTE_ROLE.ORDER_AUTH: OrderAuthResource,
    FRT_ROUTE_ROLE.ORDER_USER: OrderUserResource,
    FRT_ROUTE_ROLE.ORDER_ADDR: OrderAddressResource,
    FRT_ROUTE_ROLE.ORDER_INVOICES: InvoiceResource,
    FRT_ROUTE_ROLE.PAYMENT: PaymentResource,
}

# default url of roles
role_default_urlpatterns = {
    FRT_ROUTE_ROLE.HOMEPAGE: r'/',
    FRT_ROUTE_ROLE.USER_AUTH: r'/auth',
    FRT_ROUTE_ROLE.USER_LOGOUT: r'/logout',
    FRT_ROUTE_ROLE.USER_INFO: r'/user_info',
    FRT_ROUTE_ROLE.MY_ACCOUNT: r'/my_account',
    FRT_ROUTE_ROLE.RESET_PWD_REQ: r'/forgot_password',
    FRT_ROUTE_ROLE.RESET_PWD: r'/reset_password',
    FRT_ROUTE_ROLE.PRDT_LIST: r'/products',
    FRT_ROUTE_ROLE.TYPE_LIST: r'/type/{id_type}',
    FRT_ROUTE_ROLE.PRDT_INFO: r'/products/{id_sale}',
    FRT_ROUTE_ROLE.BASKET: r'/basket',
    FRT_ROUTE_ROLE.ORDER_LIST: r'/orders',
    FRT_ROUTE_ROLE.ORDER_INFO: r'/orders/{id_order}',
    FRT_ROUTE_ROLE.ORDER_AUTH: r'/order_auth',
    FRT_ROUTE_ROLE.ORDER_USER: r'/order_user',
    FRT_ROUTE_ROLE.ORDER_ADDR: r'/order_addr',
    FRT_ROUTE_ROLE.ORDER_INVOICES: r'/invoices/{id_order}',
    FRT_ROUTE_ROLE.PAYMENT: r'/payment',
}

# fixed urls which are not configurable in BO
fixed_urlpatterns = {
    r'/ajax_login': LoginAPIResource,
    r'/ajax_register': RegisterAPIResource,
    r'/ajax_user': UserAPIResource,
    r'/ajax_basket': BasketAPIResource,
    r'/ajax_order': OrderAPIResource,
    r'/ajax_shipping_conf': ShippingAPIResource,

    r'/paypal/{id_trans}/cancel': PaypalCancelResource,
    r'/paypal/{id_trans}/success': PaypalSuccessResource,
    r'/paypal/{id_trans}/failure': PaypalFailureResource,
    r'/paybox/{id_trans}/success': PayboxSuccessResource,
    r'/paybox/{id_trans}/failure': PayboxFailureResource,
    r'/paybox/{id_trans}/cancel': PayboxCancelResource,
    r'/paybox/{id_trans}/waiting': PayboxWaitingResource,
    r'/webservice/1.0/pub/JSONAPI': AuxResource,
    r'/webservice/1.0/pub/apikey.pem': crypto.APIPubKey,

    # static files
    r'/js/{name}': download.JsItem,
    r'/js/{subpath}/{name}': download.JsItem,
    r'/css/{name}': download.CssItem,
    r'/css/{subpath}/{name}': download.CssItem,
    r'/img/{name}': download.ImgItem,
    r'/img/{subpath}/{name}': download.ImgItem,

    # access theme assets
    r'/templates/{theme}/{file_type}/{name}': download.AssetItem,
    r'/templates/{theme}/{file_type}/{folder}/{name}': download.AssetItem,

    # static html
    r'/mention_legal': homepage.MentionLegalResource,
    r'/cgv': homepage.CGVResource,
    r'/commands_deliveries': homepage.CommandsAndDeliveriesResource,
    r'/e-shop': homepage.EShopResource,
    r'/lookbook': homepage.LookbookResource,
    r'/la-saga': homepage.LaSagaResource,
    r'/error': error.GeneralErrorResource,

    r'/new_user_email': email.NewUserEmailResource,
    r'/orders/{id_order}/email': email.OrderEmailResource,
    r'/reset_password_email': email.ResetPwdEmailResource,

    r'/vessel': vessel.VesselHomepageResource,
    r'/vessel/search': vessel.SearchResource,
    r'/vessel/quick_search': vessel.VesselQuickSearchResource,
    r'/vessel/get_vessel_navpath': vessel.VesselNavPathResource,
    r'/vessel/update_user_fleet': vessel.UserFleetResource,
    r'/vessel/update_vessel_reminder': vessel.VesselArrivalReminderResource,
    r'/vessel/update_container_reminder': vessel.ContainerArrivalReminderResource,
}


param_pattern = re.compile(r'\(.+?\)')

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
        if not resp_dict or 'routes' not in resp_dict: return

        routes = resp_dict['routes'].get('route') or []
        if not any(routes): return

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

    def url_res_mapping(self, reload_):
        urlpatterns = {}
        for url, res in fixed_urlpatterns.iteritems():
            urlpatterns[url] = res()

        if settings.PRODUCTION:
            self.refresh()
        else:
            if reload_:
                self.refresh()
            else:
                # in dev env, will send reload signal to fetch routes from
                # user server after FO is up, since routes api in users server
                # is private and need cryto key from front server.
                pass

        if self.routes_dict:
            for route in self.routes_dict.itervalues():
                meta_dict = self._get_meta_by_route(route)
                kwargs = {'title': route.get('title', ''),
                          'content': route.get('content', ''),
                          'meta': meta_dict,
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
        if self.is_routed(role):
            route = self.role_mapping[role].values()[0]
            url_pattern = self._format_url(route, '%%(%s)s')
        else:
            url_pattern = re.sub(r'{(\w+)}', lambda m: '%%(%s)s' % m.groups(),
                                 role_default_urlpatterns[role])
        return url_pattern

    def _get_res(self, role):
        return role_res_mapping.get(role, HomepageResource)

    def get_meta_by_role(self, role):
        meta = {}
        if self.is_routed(role):
            route = self.role_mapping.get(role).values()[0]
            meta = self._get_meta_by_route(route)
        return meta

    def _get_meta_by_route(self, route):
        meta = route.get('meta', None) and as_list(route['meta']) or None
        return meta and dict(map(lambda x: [x['@name'], x['#text']], meta)) or {}

    def is_routed(self, role):
        return self.role_mapping and role in self.role_mapping

    def _format_url(self, route, param_format='{%s}'):
        url_pattern = route.get('url') or ''
        params = self._get_sorted_params(route)
        groups = param_pattern.findall(url_pattern)
        for g, p in zip(groups, params):
            url_pattern = url_pattern.replace(g, param_format % p['#text'], 1)
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

