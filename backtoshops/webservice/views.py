# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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


import base64
import cgi
import logging
import json
import math
import ujson
import settings
from collections import defaultdict
from datetime import date
from datetime import datetime
from incf.countryutils import transformations

from django.contrib.auth import authenticate as _authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max
from django.db.models import F
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import View, ListView, DetailView, TemplateView
from django.views.decorators.csrf import csrf_exempt

from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.constant import SERVICES
from B2SUtils.common import to_round
from B2SUtils.redis_cli import redis_cli

from accounts.models import UserProfile
from address.models import Address
from attributes.models import BrandAttributePreview
from attributes.models import CommonAttribute
from accounts.models import Brand
from barcodes.models import Barcode
from brandings.models import Branding
from brandsettings.models import BrandSettings
from brandsettings.models import InvoiceNumber
from common.cache_invalidation import send_cache_invalidation
from common.filter_utils import get_filter, get_order_by
from common.constants import USERS_ROLE
from common.constants import SUCCESS, FAILURE
from common.error import InvalidRequestError
from common.error import ParamsValidCheckError
from common.fees import compute_fee
from common.transaction import remote_payment_init
from common.utils import get_default_setting
from events.models import Event
from events.models import EventQueue
from globalsettings import get_setting
from globalsettings.models import GlobalSettings
from routes.models import Route
from sales.models import ProductCategory
from sales.models import ProductType
from sales.models import STOCK_TYPE_GLOBAL
from sales.models import Sale
from sales.models import ShopsInSale
from sales.models import TypeAttributeWeight
from sales.utils import get_sale_external_id
from sales.utils import get_sale_orig_price
from sales.utils import get_sale_discounted_price
from sales.utils import get_sale_premium
from shippings.models import CustomShippingRateInShipping
from shippings.models import CustomShippingRate
from shippings.models import SC_CARRIER_SHIPPING_RATE
from shippings.models import SC_CUSTOM_SHIPPING_RATE
from shippings.models import SC_FLAT_RATE
from shippings.models import STOY_PRICE, STOY_WEIGHT, STOY_COUNTRY, STOY_REGION
from shippings.models import FlatRateInShipping
from shippings.models import ServiceInShipping
from shippings.models import Carrier, Service
from shops.models import Shop
from stocks.views import OutOfStockError
from stocks.views import update_stock
from taxes.models import Rate

from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS

fail = lambda s: HttpResponse(json.dumps({'success': False, 'error': s}), mimetype='text/json')

class BaseWebservice(View):
    def render_to_response(self, context, **response_kwargs):
        response_kwargs.update({
            'mimetype': 'text/xml'
        })
        return super(BaseWebservice, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update({
            "settings": settings,
        })
        return kwargs

#
# Public webservices
#

class SalesListView(BaseWebservice, ListView):
    template_name = "sales_list.xml"

    def get_queryset(self):
        product_type = self.request.GET.get('type', None)
        category = self.request.GET.get('category', None)
        shop = self.request.GET.get('shop', None)
        brand = self.request.GET.get('brand', None)
        queryset = Sale.objects.filter(
            product__valid_from__lte=date.today()
        ).filter(
            Q(product__valid_to__isnull=True) |
            Q(product__valid_to__gte=date.today())
        )
        if product_type:
            queryset = queryset.filter(product__type=product_type)
        if category:
            queryset = queryset.filter(product__category=category)
        if shop:
            queryset = queryset.filter(shops__in=[shop])
        if brand:
            queryset = queryset.filter(mother_brand=brand)

        return queryset

class ShopsListView(BaseWebservice, ListView):
    template_name = "shops_list.xml"

    def get_queryset(self):
        brand = self.request.GET.get('seller', None)
        city = self.request.GET.get('city', None)
        queryset = Shop.objects.all()
        if brand:
            queryset = queryset.filter(mother_brand=brand)
        if city:
            queryset = queryset.filter(city__iexact=city)
        return queryset

class TypesListView(BaseWebservice, ListView):
    template_name = "types_list.xml"

    def get_queryset(self):
        queryset = ProductType.objects.filter(brand_id=self.id_brand)
        self.q_category = ProductCategory.objects.filter(brand_id=self.id_brand)
        return queryset

    def get(self, request, brand, *args, **kwargs):
        self.id_brand = brand
        return super(TypesListView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update({
            'categories': self.q_category
        })
        return kwargs

class BrandSettingsView(BaseWebservice, ListView):
    template_name = "brandsettings_list.xml"

    def get_queryset(self):
        settings = []
        for s in GlobalSettings.objects.all():
            settings.append({
                'brand_id': '',
                'key': s.key,
                'value': s.value
            })
        for s in BrandSettings.objects.filter(shopowner=None):
            settings.append({
                'brand_id': s.brand_id,
                'key': s.key,
                'value': s.value
            })
        return settings

class BrandListView(BaseWebservice, ListView):
    template_name = "brand_list.xml"

    def get_queryset(self):
        product_type = self.request.GET.get('type', None)
        category = self.request.GET.get('category', None)
        queryset = Brand.objects.all()
        if product_type:
            queryset = queryset.filter(sales__product__type=product_type).distinct()
        if category:
            queryset = queryset.filter(sales__product__category=category).distinct()
        return queryset

class BrandInfoView(BaseWebservice, DetailView):
    template_name = "brand_info.xml"
    model = Brand

class BrandingsListView(BaseWebservice, ListView):
    template_name = "brandings_slideshow.xml"
    def get(self, request, brand, *args, **kwargs):
        self.id_brand = brand
        return super(BrandingsListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        return Branding.objects.filter(for_brand_id=self.id_brand)\
                   .exclude(show_from__gt=datetime.now())\
                   .exclude(show_until__lt=datetime.now())\
                   .order_by('sort_key')[:5]

class SalesInfoView(BaseWebservice, DetailView):
    template_name = "sales_info.xml"
    model = Sale

class ShopsInfoView(BaseWebservice, DetailView):
    template_name = "shops_info.xml"
    model = Shop

class TypesInfoView(BaseWebservice, DetailView):
    template_name = "types_info.xml"
    model = ProductType

class SalesFindView(BaseWebservice, ListView):
    template_name = "sales_list.xml"

    def get_queryset(self):
        search = self.request.GET.get('search', None)
        filters = self.request.GET.getlist('filter', [])
        sorteds = self.request.GET.getlist('sorted', [])

        queryset = Sale.objects.filter(
                Q(product__name__icontains=search)|
                Q(product__description__icontains=search)|
                Q(mother_brand__name__icontains=search)|
                Q(product__type__name__icontains=search)|
                Q(product__brand_attributes__name__icontains=search)).distinct()

        if filters and not isinstance(filters, list):
            filters = [filters]

        if sorteds and not isinstance(sorteds, list):
            sorteds = [sorteds]

        q = None
        for f in filters:
            f = json.loads(f)
            q = get_filter(f['parameter'])(f['operator'],
                                           f['comparison'],
                                           f['value'], q).toQ()
        if q:
            queryset = queryset.filter(q)

        orderby = []
        for o in sorteds:
            o = json.loads(o)
            orderby.append(get_order_by(o['parameter'], o['order']))

        if orderby:
            queryset = queryset.annotate(max__product__brand_attributes=Max('product__brand_attributes'))
            queryset = queryset.order_by(*tuple(orderby)).distinct()

        return queryset

#
# APIs for managing shop inventory
#

def basic_auth(func):
	"""Decorator for basic auth"""
	def wrapper(request, *args, **kwargs):
            try:
                if is_authenticated(request):
                    return func(request, *args, **kwargs)
                else:
                    return HttpResponseForbidden()
            except Exception, ex:
                return HttpResponse(json.dumps({'success': False, 'error': ex.message}), mimetype='text/json')
	return wrapper

def is_authenticated(request):
    token = request.META['HTTP_AUTHORIZATION'].replace('Basic ', '')
    username, password = base64.decodestring(token).split(':')
    user = _authenticate(username=username, password=password)

    if not user:
        return False

    try:
        shop = Shop.objects.get(upc=request.REQUEST['shop'])
    except Shop.DoesNotExist:
        raise Exception("Shop %s doesn't exist." % request.REQUEST['shop'])

    if user.is_staff:
        return (shop.mother_brand.employee.filter(user__id=user.id).count() > 0)
    else: #operator
        return (shop.userprofile_set.filter(user__id=user.id).count() > 0)

@csrf_exempt
def authenticate(request):
    token = request.META['HTTP_AUTHORIZATION'].replace('Basic ', '')
    username, password = base64.decodestring(token).split(':')
    user = _authenticate(username=username, password=password)
    if user:
        return HttpResponse(json.dumps({'success': True}), mimetype='text/json')
    else:
        return HttpResponseForbidden()

def get_sale(shop_upc, item):
    try:
        barcode = Barcode.objects.get(upc=item)
        shop = Shop.objects.get(upc=shop_upc)
        sales = Sale.objects.filter(barcodes__in=[barcode], shops__in=[shop])
        if sales.count() > 0:
            return sales[0], barcode
        return None, None
    except Exception, ex:
        return None, None

def _stock_setter(request, flag):
    data = decrypt_json_resp(
        request,
        settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
        settings.PRIVATE_KEY_PATH)
    data = json.loads(data)
    try:
        content = {'success': True}
        for params in data:
            if params['fake_for_coupon']:
                continue
            update_stock(params['id_sale'], params['id_variant'],
                         params['id_type'], params['id_shop'],
                         delta_stock=params['quantity'] * flag)
    except OutOfStockError, e:
        logging.error('Failed to update stock due to out of stock: %s',
                      e.args[0], exc_info=True)
        content = {'success': False,
                   'errmsg': e.args[0]}

    except Exception, e:
        logging.error('Failed to update stock: %s, data: %s',
                      e, data, exc_info=True)
        content = {'success': False}

    content = json.dumps(content)
    content = gen_encrypt_json_context(
        content,
        settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
        settings.PRIVATE_KEY_PATH
    )
    return HttpResponse(content, mimetype='application/json')


def _stock_setter_by_barcode(request, val):
    token = request.META['HTTP_AUTHORIZATION'].replace('Basic ', '')
    username, password = base64.decodestring(token).split(':')
    user = _authenticate(username=username, password=password)

    try:
        shop_upc = request.REQUEST['shop']
        shop = Shop.objects.get(upc=shop_upc)
    except:
        return fail('shop upc must be given')

    sale, barcode = get_sale(shop_upc, request.REQUEST['item'])
    if sale is None or barcode is None:
        return fail('sale not found with given shop and item')

    if not user.is_staff or shop not in user.get_profile().shops.all():
        #this operator can't touch this shop.
        return fail('no access to this shop''s stock')

    #if shop is frozen.
    try:
        if ShopsInSale.objects.get(shop=shop, sale=sale).is_freezed:
            return fail("this shop is frozen, can't update stocks")
    except:
         return fail('shop is not found in this sale')

    try:
        update_stock(sale.id,
                     barcode.brand_attribute_id,
                     barcode.common_attribute_id,
                     shop.id,
                     delta_stock=val)
    except:
        return fail('stock of the given shop is invalid.')

    return HttpResponse(json.dumps({
            'success': True,
            'total_stock': sale.total_stock,
            'total_rest_stock': sale.total_rest_stock
        }), mimetype='text/json')

@csrf_exempt
def stock_increment(request):
    return _stock_setter(request, 1)

@csrf_exempt
def stock_decrement(request):
    return _stock_setter(request, -1)

@csrf_exempt
@basic_auth
def barcode_increment(request):
    return _stock_setter_by_barcode(request, 1)

@csrf_exempt
@basic_auth
def barcode_decrement(request):
    return _stock_setter_by_barcode(request, -1)

@csrf_exempt
@basic_auth
def barcode_returned(request):
    return _stock_setter_by_barcode(request, 1)


EARTH_MEAN_RADIUS = 6371 * 1000 * 1000 # 6371 km
LATITUDE_METERS = 111.2 * 1000 * 1000 # 111.2 km
LONGITUDE_METERS = ''

def filter_by_coordinate(query_set, lat, lng, radius):
    try:
        import pymongo
        from bson.son import SON

        db = pymongo.Connection().backtoshops
        ret = db.command(SON([('geoNear', 'shops'), ('near', [float(lng), float(lat)]), ('spherical', True), ('maxDistance', float(radius) / 1000 / 6371)]))
        shops = [item['obj']['shop_id'] for item in ret['results']]
        return query_set.filter(pk__in=shops)
    except:
        lat, lng, radius = float(lat), float(lng), float(radius)
        lat_delta = radius / LATITUDE_METERS
        lat_min, lat_max = lat - lat_delta, lat + lat_delta
        lng_delta = abs(radius / (math.pi / 180 * EARTH_MEAN_RADIUS * math.cos(abs(lng) / 2 * math.pi)))
        lng_min, lng_max = lng - lng_delta, lng + lng_delta
    #    print 'lat delta', lat_delta
    #    print 'lng delta', lng_delta
    #    print lat_min, lat_max, lng_min, lng_max
        return query_set.filter(latitude__gte=lat_min, latitude__lte=lat_max, longitude__gte=lng_min, longitude__lte=lng_max)


class VicinitySalesListView(BaseWebservice, ListView):
    template_name = "sales_list.xml"

    def get_queryset(self):
        lat, lng = self.request.GET.get('lat', None), self.request.GET.get('lng', None)
        radius = self.request.GET.get('radius', None)
        product_type = self.request.GET.get('type', None)
        category = self.request.GET.get('category', None)
        shop = self.request.GET.get('shop', None)
        brand = self.request.GET.get('brand', None)
        queryset = Sale.objects.filter(
            product__valid_from__lte=date.today()
        ).filter(
            Q(product__valid_to__isnull=True) |
            Q(product__valid_to__gte=date.today())
        )
        if product_type:
            queryset = queryset.filter(product__type=product_type)
        if category:
            queryset = queryset.filter(product__category=category)
        if shop:
            queryset = queryset.filter(shops__in=[shop])
        if brand:
            queryset = queryset.filter(mother_brand=brand)
        if lat and lng and radius:
            shops = filter_by_coordinate(Shop.objects.all(), lat, lng, radius)
            queryset = queryset.filter(shops__in=shops)
        return queryset

class VicinityShopsListView(BaseWebservice, ListView):
    template_name = "shops_list.xml"

    def get_queryset(self):
        lat, lng = self.request.GET.get('lat', None), self.request.GET.get('lng', None)
        radius = self.request.GET.get('radius', None)
        brand = self.request.GET.get('seller', None)
        city = self.request.GET.get('city', None)
        queryset = Shop.objects.all()
        if brand:
            queryset = queryset.filter(mother_brand=brand)
        if city:
            queryset = queryset.filter(city__iexact=city)
        if lat and lng and radius:
            queryset = filter_by_coordinate(queryset, lat, lng, radius)
        return queryset

def apikey(dummy=None):
    with open(settings.PUB_KEY_PATH) as f:
        key = f.read()
        f.close()
        return HttpResponse(key)


@csrf_exempt
def event_push(request, *args, **kwargs):
    try:
        query = decrypt_json_resp(
            request,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH)
        args = cgi.parse_qs(query)
        event_id = args.get('event', [''])[0]
        if not event_id or not event_id.isdigit():
            raise InvalidRequestError('missing event')

        handler_params = {}
        event = Event.objects.get(pk=event_id)
        for param in event.event_handler_params.get_query_set():
            handler_params[param.name] = args.get(param.name, [param.value])[0]

        new = EventQueue()
        new.event_id = event_id
        new.param_values = json.dumps(handler_params)
        new.save()

        content = {'result': SUCCESS}
    except Exception, e:
        logging.error('event_push_failure: %s' % e, exc_info=True)
        content = {'result': FAILURE}

    content = gen_encrypt_json_context(
        ujson.dumps(content),
        settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
        settings.PRIVATE_KEY_PATH
    )
    return HttpResponse(content, mimetype='application/json')


class BaseCryptoWebService(BaseWebservice):
    from_ = SERVICES.USR

    def render_to_response(self, context, **response_kwargs):
        resp = super(BaseCryptoWebService, self).render_to_response(context, **response_kwargs)
        debugging = self.request.GET.get('debugging', False)
        if settings.CRYPTO_RESP_DEBUGING and debugging:
            return resp
        resp.render()
        return self._get_crypto_resp(resp.content, **response_kwargs)

    def _get_crypto_resp(self, content, **response_kwargs):
        if self.request.method == 'GET':
            self.from_ = self.request.GET.get('from', SERVICES.USR)
        elif self.request.method == 'POST':
            self.from_ = self.request.POST.get('from', SERVICES.USR)
        content = gen_encrypt_json_context(
            content,
            settings.SERVER_APIKEY_URI_MAP[self.from_],
            settings.PRIVATE_KEY_PATH)
        response_kwargs.update({
            'mimetype': 'application/json'
        })

        return HttpResponse(content, **response_kwargs)


class EventListView(BaseCryptoWebService, ListView):
    template_name = "event_list.xml"

    def get_queryset(self):
        queryset = Event.objects.all()
        return queryset

    def get_context_data(self, **kwargs):
        context = super(EventListView, self).get_context_data(**kwargs)
        context['default_handler_url'] = '/webservice/1.0/private/event/push'
        return context


class RoutesListView(BaseCryptoWebService, ListView):
    template_name = "routes_list.xml"

    def get_queryset(self):
        brand = self.request.GET.get('brand', None)

        queryset = Route.objects.all()
        if brand:
            queryset = queryset.filter(mother_brand=brand).distinct()

        return queryset


class TaxesListView(BaseCryptoWebService, ListView):
    template_name = "taxes_list.xml"

    def get_queryset(self):
        fromCountry = self.request.GET.get('fromCountry', None)
        fromProvince = self.request.GET.get('fromProvince', None)
        toCountry = self.request.GET.get('toCountry', None)
        toProvince = self.request.GET.get('toProvince', None)

        queryset = Rate.objects.filter(enabled=True)
        if fromCountry:
            queryset = queryset.filter(region_id=fromCountry)
        if toCountry:
            queryset = queryset.filter(shipping_to_region_id=toCountry)
        if fromProvince:
            queryset = queryset.filter(province=fromProvince)
        if toProvince:
            queryset = queryset.filter(shipping_to_province=toProvince)

        return queryset

    def get_context_data(self, **kwargs):
        fromCountry = self.request.GET.get('fromCountry', None)
        fromProvince = self.request.GET.get('fromProvince', None)
        kwargs.update({'country': fromCountry})
        if fromProvince:
            kwargs.update({'province': fromProvince})
        return kwargs


def populate_carriers(carrier_services=None, shipping=None):
    if not carrier_services and not shipping:
        return []

    if carrier_services:
        carrier_services = dict(carrier_services)
    else:
        carrier_services = defaultdict(list)
    if shipping:
        services_in_shipping = ServiceInShipping.objects.filter(
            shipping=shipping)
        for item in services_in_shipping:
            carrier_services[item.service.carrier.pk].append(item.service.pk)

    if not carrier_services:
        raise ParamsValidCheckError("invalid_shipping_or_carrier_services: "
                                    "shipping-%s, carrier_services-%s"
                                    % (shipping, carrier_services))
    carriers = Carrier.objects.filter(pk__in=carrier_services.keys())
    for carrier in carriers:
        kwargs = {'carrier': carrier}
        services_id = carrier_services.get(carrier.pk)
        if services_id:
            kwargs['pk__in'] = services_id
        services = Service.objects.filter(**kwargs)
        setattr(carrier, 'carrier_services', services)

    return carriers

def populate_carrier_and_custom_services(carrier_services_map):
    """
    @param carrier_services_map:
           carrier services map tuple list:
                [(carrier_id1, [service_1, service_2]), ...]
                carrier_id(0) is for custom services.
    """
    custom_services = []
    carrier_services = []
    for item in carrier_services_map:
        if int(item[0]) == 0:
            custom_services.extend(item[1])
        else:
            carrier_services.append(item)

    if custom_services:
        custom_rules = get_custom_rules_by_id(custom_services)
    else:
        custom_rules = []

    carrier_rules = populate_carriers(carrier_services)
    return custom_rules, carrier_rules

def get_custom_rules_by_shipping(shipping):
    kwargs = {'shipping': shipping}
    rules_in_shipping = CustomShippingRateInShipping.objects.filter(**kwargs)
    return [item.custom_shipping_rate for item in rules_in_shipping]

def get_custom_rules_by_id(custom_rules):
    if custom_rules:
        kwargs = {'pk__in': custom_rules}
        return CustomShippingRate.objects.filter(**kwargs)
    else:
        return CustomShippingRate.objects.all()

def populate_shipping_rate(sale):
    """ populate carrier/custom/flat shipping rate
    """
    sp_calc_method = sale.shippinginsale.shipping.shipping_calculation
    shipping = sale.shippinginsale.shipping
    if sp_calc_method == SC_CARRIER_SHIPPING_RATE:
        carriers = populate_carriers(shipping=shipping)
        setattr(sale, 'carriers', carriers)

    elif sp_calc_method == SC_CUSTOM_SHIPPING_RATE:
        custom_rules = get_custom_rules_by_shipping(shipping)
        setattr(sale, 'custom_rules', custom_rules)

    elif sp_calc_method == SC_FLAT_RATE:
        ft_in_shipping = FlatRateInShipping.objects.get(shipping=shipping)
        setattr(sale,
                'flat_rate',
                ft_in_shipping.flat_rate)
    return sale

class ShippingInfoView(BaseCryptoWebService, ListView):
    template_name = "shipping_info.xml"

    def requestValidCheck(self):
        sales = self.request.GET.get('sales', None)
        try:
            if not sales:
                raise ParamsValidCheckError(
                    "shipping_info_view_Miss_param: %s"
                    % self.request.GET)
            sales = json.loads(sales)
            for sale_id, props in sales:
                if ('variant' not in props or
                    'weight_type' not in props):
                    raise ValueError("Miss variant or type attribute")

        except ValueError, e:
            logging.error('shipping_info_valid_check_failure: %s'
                          % e, exc_info=True)
            raise ParamsValidCheckError(
                "shipping_info_view_Invalid_sale_param: %s"
                % sales)
        return sales

    def typeAttrValidCheck(self, sale, type_attr_id):
        # type_attr_id is None or 0 means no type attribute selected.
        if type_attr_id is None or int(type_attr_id) == 0:
            return

        try:
            tp_attr = CommonAttribute.objects.get(pk=type_attr_id)
        except ObjectDoesNotExist, e:
            logging.error('shipping_info_type_attr_check_failure:'
                          '%s' % e, exc_info=True)
            error = ("shipping_info_invalid_type_attr:"
                     "sale: %s, type_attr: %s"
                     % (sale.pk, type_attr_id))
            raise ParamsValidCheckError(error)

        if tp_attr.for_type != sale.product.type:
            error = ("shipping_info_inconsistent_type_attr:"
                     "sale: %s, type_attr: %s"
                     % (sale.pk, type_attr_id))
            raise ParamsValidCheckError(error)
        return tp_attr

    def brandAttrValidCheck(self, sale, variant_id):
        # variant_id is None or 0 means no brand attribute selected.
        if variant_id is None or int(variant_id) == 0:
            return

        br_attr_prevs = BrandAttributePreview.objects.filter(
            product_id=sale.product.pk, brand_attribute_id=variant_id)
        if len(br_attr_prevs) > 0:
            br_attr_prev = br_attr_prevs[0]
        else:
            error = ("shipping_info_invlaid_brand_attr:"
                     "sale: %s, brand_attr: %s"
                     % (sale.pk, variant_id))
            logging.error('shipping_info_brand_attr_check_failure:'
                          '%s' % error)
            raise ParamsValidCheckError(error)

        return br_attr_prev.brand_attribute

    def typeAttributeWeightValidCheck(self, sale, type_attr):
        if type_attr is None:
            return

        try:
            tp_attr_weight = TypeAttributeWeight.objects.get(
                sale=sale, type_attribute=type_attr)
        except ObjectDoesNotExist, e:
            logging.error('shipping_info_type_attr_weight_check_failure:'
                          '%s' % e, exc_info=True)
            error = ("shipping_info_invlaid_type_attr_for_weight:"
                     "sale: %s, type attr: %s"
                     % (sale.pk, type_attr.pk))
            raise ParamsValidCheckError(error)
        return tp_attr_weight

    def get_queryset(self):
        sales = self.requestValidCheck()

        queryset = []
        for sale_id, prop in sales:
            try:
                sale = Sale.objects.get(pk=sale_id)
            except ObjectDoesNotExist, e:
                logging.warning("shipping_info_sale_not_exist:"
                                "sale-%s" % sale_id)
                continue


            type_attr_id = prop['weight_type']
            variant_id = prop['variant']
            type_attr = self.typeAttrValidCheck(sale, type_attr_id)
            brand_attr = self.brandAttrValidCheck(sale, variant_id)
            tp_attr_weight = self.typeAttributeWeightValidCheck(sale, type_attr)

            setattr(sale, 'type_attribute', type_attr)
            setattr(sale, 'brand_attribute', brand_attr)

            if not tp_attr_weight:
                weight = sale.product.standard_weight
            else:
                weight = tp_attr_weight.type_attribute_weight

            setattr(sale, 'weight', weight)

            populate_shipping_rate(sale)
            queryset.append(sale)

        return queryset


class ShippingFeesView(BaseCryptoWebService, ListView):
    template_name = "shipping_fees.xml"

    def get_context_data(self, **kwargs):
        carrier_rules, custom_rules = kwargs.get('object_list') or ([], [])
        kwargs['carrier_rules'] = carrier_rules
        kwargs['custom_rules'] = custom_rules
        return kwargs

    def get_queryset(self):
        carrier_services_map = self.request.GET.get('carrier_services', None)
        weight = self.request.GET.get('weight')
        weight_unit = self.request.GET.get('unit')
        dest = self.request.GET.get('dest')
        id_address = self.request.GET.get('id_address')
        amount = self.request.GET.get('amount')

        if carrier_services_map:
            carrier_services_map = json.loads(carrier_services_map)

        if (weight is None or
            weight_unit is None or
            dest is None or
            not carrier_services_map or
            not id_address):
            raise InvalidRequestError(
                "invalide_shipping_fees_request_miss_params %s"
                % self.request.GET)

        custom_rules, carrier_rules = populate_carrier_and_custom_services(
            carrier_services_map)

        orig = self.get_orig_address(id_address)
        # calculate fees for services.
        for carrier in carrier_rules:
            for service in carrier.carrier_services:
                data = {'carrier': carrier.pk,
                        'addr_orig': orig,
                        'addr_dest': dest,
                        'service': service.pk,
                        'weight': weight,
                        'weight_unit': weight_unit}
                fee = compute_fee(data)
                setattr(service, 'shipping_fee', fee)

        dest_addr = ujson.loads(dest)
        matched_custom_rules = []
        for custom_rule in custom_rules:
            if custom_rule.total_order_type == STOY_PRICE:
                pass #TODO
            elif custom_rule.total_order_type == STOY_WEIGHT:
                pass #TODO
            elif custom_rule.total_order_type == STOY_COUNTRY:
                if self._addr_in_france(dest_addr) and (not amount
                        or float(custom_rule.total_order_lower) <= float(amount) < float(custom_rule.total_order_upper)):
                    matched_custom_rules.append(custom_rule)
            elif custom_rule.total_order_type == STOY_REGION:
                if self._addr_in_europe(dest_addr) and (not amount
                        or float(custom_rule.total_order_lower) <= float(amount) < float(custom_rule.total_order_upper)):
                    matched_custom_rules.append(custom_rule)
        return [carrier_rules, matched_custom_rules or custom_rules]

    def _addr_in_france(self, dest_addr):
        return dest_addr['country'] == 'FR'

    def _addr_in_europe(self, dest_addr):
        return not self._addr_in_france(dest_addr) \
           and transformations.cca_to_ctn(dest_addr['country']) == 'Europe'

    def get_orig_address(self, id_address):
        addr = Address.objects.get(pk=id_address)
        address = {'address': addr.address,
                   'city': addr.city,
                   'country': addr.country,
                   'province': addr.province_code,
                   'postalcode': addr.zipcode}
        return address


class ShippingServicesInfoView(BaseCryptoWebService, ListView):
    template_name = "shipping_services_info.xml"

    def get_context_data(self, **kwargs):
        carrier_rules, custom_rules = kwargs.get('object_list') or ([], [])
        kwargs['carrier_rules'] = carrier_rules
        kwargs['custom_rules'] = custom_rules
        return kwargs

    def get_queryset(self):
        carrier_services_map = self.request.GET.get('carrier_services', None)
        id_sale = self.request.GET.get('id_sale', None)
        if carrier_services_map:
            carrier_services_map = json.loads(carrier_services_map)
        elif id_sale:
            carrier_services_map = self._get_services_by_sale(id_sale)

        if not carrier_services_map:
            return []

        custom_rules, carrier_rules = populate_carrier_and_custom_services(
            carrier_services_map)

        return [carrier_rules, custom_rules]

    def _get_services_by_sale(self, id_sale):
        sale = Sale.objects.get(pk=id_sale)
        cu_sr = SHIPPING_CALCULATION_METHODS.CUSTOM_SHIPPING_RATE
        ca_sr = SHIPPING_CALCULATION_METHODS.CARRIER_SHIPPING_RATE
        sale_shipping = sale.shippinginsale.shipping

        if sale_shipping.shipping_calculation == cu_sr:
            services = self._get_sale_custom_services(sale_shipping)
        elif sale_shipping.shipping_calculation == ca_sr:
            services = self._get_sale_carrier_services(sale_shipping)
        else:
            services = []

        return services

    def _get_sale_custom_services(self, shipping):
        custom_rules = get_custom_rules_by_shipping(shipping)
        return [0, custom_rules]

    def _get_sale_carrier_services(self, shipping):
        services = ServiceInShipping.objects.filter(shipping=shipping)

        carrier_services = defaultdict(list)
        for serv_in_shipping in services:
            service = serv_in_shipping.service
            carrier_services[service.carrier_id].append(service.pk)
        return carrier_services.items()

class InvoiceView(BaseCryptoWebService, ListView):
    template_name = "invoice.xml"

    def get_queryset(self):
        is_business_account = \
                self.request.GET.get('is_business_account') == 'True'
        if is_business_account is None:
            is_business_account = False
            if get_setting('front_personal_account_allowed') == 'False' and \
                    get_setting('front_business_account_allowed') == 'True':
                is_business_account = True

        customer_name = self.request.GET.get('customer')
        company_name = self.request.GET.get('company_name') or ''
        company_position = self.request.GET.get('company_position') or ''
        company_tax_id = self.request.GET.get('company_tax_id') or ''
        dest = self.request.GET.get('dest')
        shipping_fee = self.request.GET.get('shipping_fee')
        handling_fee = self.request.GET.get('handling_fee')
        carrier = self.request.GET.get('carrier')
        service = self.request.GET.get('service')
        content = self.request.GET.get('content')
        id_shop = int(self.request.GET.get('shop'))
        id_brand = int(self.request.GET.get('brand'))
        self.id_brand = id_brand

        seller = self.get_seller(id_shop, id_brand)
        buyer = self.get_buyer(customer_name, is_business_account,
            company_name, company_position, company_tax_id, dest)
        from_address = seller['address']
        to_address = buyer['address']
        items, items_gross, items_tax, currency = self.get_items(
            content,
            from_address,
            to_address,
            is_business_account)
        shipping, shipping_gross, shipping_tax = self.get_shipping(
            handling_fee,
            shipping_fee,
            carrier,
            service,
            from_address,
            to_address,
            is_business_account)
        shipping.update(self.get_shipping_period(id_brand, id_shop))

        gross = items_gross + shipping_gross
        tax = items_tax + shipping_tax
        total = gross
        if not self.get_use_after_tax_price():
            total += tax
        invoice = {
            'number': self.invoice_number(id_brand, id_shop),
            'date': datetime.now().date().strftime('%Y-%m-%d'),
            'currency': currency,
            'seller': seller,
            'buyer': buyer,
            'items': items,
            'shipping': shipping,
            'total': {'gross': gross,
                      'tax': tax,
                      'total': total},
            'payment': self.get_payment(id_brand, id_shop),
        }

        return [invoice]

    def get_use_after_tax_price(self):
        try:
            val = BrandSettings.objects.get(key='use_after_tax_price',
                                            brand_id=self.id_brand,
                                            shopowner=None).value
            return val == 'True'
        except BrandSettings.DoesNotExist:
            return False

    def brand_seller(self, id_brand):
        brand = Brand.objects.get(pk=id_brand)
        return {'name': brand.name,
                'img': brand.logo.url if brand.logo else '',
                'business': brand.business_reg_num,
                'tax': brand.tax_reg_num,
                #'personal': ?xxx,
                'address': {'addr': brand.address.address,
                            'zip': brand.address.zipcode,
                            'city': brand.address.city,
                            'province': brand.address.province_code,
                            'country': brand.address.country_id}

                }

    def shop_seller(self, id_shop):
        shop = Shop.objects.get(pk=id_shop)
        return {'name': shop.name,
                'img': shop.image.url if shop.image else '',
                'business': shop.business_reg_num,
                'tax': shop.tax_reg_num,
                #'personal': ?xxx,
                'address': {'addr': shop.address.address,
                            'zip': shop.address.zipcode,
                            'city': shop.address.city,
                            'province': shop.address.province_code,
                            'country': shop.address.country_id}
                }

    def get_seller(self, id_shop, id_brand):
        if id_shop == 0:
            return self.brand_seller(id_brand)
        else:
            return self.shop_seller(id_shop)

    def get_buyer(self, customer_name, is_business_account,
                  company_name, company_position, company_tax_id, dest):
        dest = json.loads(dest)

        buyer = {'name': dest['full_name'] or customer_name,
                 'address': dest}
        if is_business_account:
            buyer.update({
                'company_name': company_name,
                'company_position': company_position,
                'company_tax_id': company_tax_id,
            })
        return buyer

    def get_items(self, content, from_address, to_address,
                  is_business_account):
        content = json.loads(content)

        item_list = []
        gross = 0.0
        total_tax = 0.0
        currency = None
        cate_id = None
        use_after_tax_price = self.get_use_after_tax_price()
        for item in content:
            qty = item['quantity']
            item_info = {
                'id_item': item['id_item'],
                'name': item['name'],
                'type_name': item['type_name'],
                'qty': qty,
                'promo': item['promo'],
                'free': item['price'] == 0,
            }
            if item['promo'] and item['price'] < 0:
                orig_price = discounted_price = price = item['price']
                premium = 0
                external_id = ''
                desc = item['desc']
                # use last item's cate_id
            else:
                sale = Sale.objects.get(pk=item['id_sale'])
                if item['promo'] and item['price'] == 0:
                    orig_price = discounted_price = price = item['price']
                    premium = 0
                else:
                    orig_price = get_sale_orig_price(sale, item['id_price_type'])
                    discounted_price = get_sale_discounted_price(
                        sale, orig_price=orig_price)
                    premium = get_sale_premium(discounted_price, item.get('id_variant'))
                    price = discounted_price + premium

                external_id = get_sale_external_id(item['id_sale'],
                                                   item.get('id_variant'),
                                                   item.get('id_type'))
                desc = sale.product.description
                cate_id = sale.product.category.id

            items_taxes = self.get_tax(price,
                                       cate_id,
                                       from_address,
                                       to_address,
                                       is_business_account=is_business_account)
            for tax in items_taxes:
                tax['tax'] = tax['tax'] * qty
                tax['amount'] = tax['amount'] * qty

            item_info.update({
                'external_id': external_id,
                'desc': desc,
                'price': {
                    'original': orig_price,
                    'discounted': discounted_price,
                },
                'premium': premium,
                'taxes': items_taxes,
            })

            subtotal = price * qty
            for tax in items_taxes:
                if not use_after_tax_price:
                    subtotal += tax['tax']
                total_tax += tax['tax']

            item_info['subtotal'] = subtotal
            item_list.append(item_info)
            gross += price * qty
            currency = sale.product.currency.code
        return item_list, gross, total_tax, currency

    def get_tax(self, price, pro_category, from_address, to_address,
                shipping_tax=False, is_business_account=False):
        f_ctry = from_address['country']
        f_prov = from_address['province']
        t_ctry = to_address['country']
        t_prov = to_address['province']

        query = Q(enabled=True)
        if f_ctry != t_ctry:
            # tax conditions for different country
            query = (
                query &
                (
                    (Q(region_id=f_ctry) &
                     Q(province='') &
                     Q(shipping_to_region_id=None) &
                     Q(shipping_to_province='')) |
                    (Q(region_id=f_ctry) &
                     Q(province=f_prov) &
                     Q(shipping_to_region_id=None) &
                     Q(shipping_to_province="")) |
                    (Q(region_id=f_ctry) &
                     Q(province="") &
                     Q(shipping_to_region_id=t_ctry) &
                     Q(shipping_to_province="")) |
                    (Q(region_id=f_ctry) &
                     Q(province=f_prov) &
                     Q(shipping_to_region_id=t_ctry) &
                     Q(shipping_to_province=t_prov))
                )
            )
        elif f_prov != t_prov:
            # tax condition for same country, diff province
            query = (
                query &
                (
                    (Q(display_on_front=True) &
                     Q(region_id=f_ctry) &
                     Q(province='') &
                     Q(shipping_to_region_id=None) &
                     Q(shipping_to_province='')) |
                    (Q(display_on_front=True) &
                     Q(region_id=f_ctry) &
                     Q(province=f_prov) &
                     Q(shipping_to_region_id=None) &
                     Q(shipping_to_province="")) |
                    (Q(region_id=f_ctry) &
                     Q(province="") &
                     Q(shipping_to_region_id=t_ctry) &
                     Q(shipping_to_province="")) |
                    (Q(region_id=f_ctry) &
                     Q(province=f_prov) &
                     Q(shipping_to_region_id=t_ctry) &
                     Q(shipping_to_province="")) |
                    (Q(region_id=f_ctry) &
                     Q(province="") &
                     Q(shipping_to_region_id=t_ctry) &
                     Q(shipping_to_province=t_prov)) |
                    (Q(region_id=f_ctry) &
                     Q(province=f_prov) &
                     Q(shipping_to_region_id=t_ctry) &
                     Q(shipping_to_province=t_prov))
                )
            )
        else:
            # tax condition for same country, same province
            query = (
                query &
                (
                    (Q(display_on_front=True) &
                     Q(region_id=f_ctry) &
                     Q(province='') &
                     Q(shipping_to_region_id=None) &
                     Q(shipping_to_province='')) |
                    (Q(display_on_front=True) &
                     Q(region_id=f_ctry) &
                     Q(province=f_prov) &
                     Q(shipping_to_region_id=None) &
                     Q(shipping_to_province="")) |
                    (Q(region_id=f_ctry) &
                     Q(province="") &
                     Q(shipping_to_region_id=t_ctry) &
                     Q(shipping_to_province="")) |
                    (Q(region_id=f_ctry) &
                     Q(province=f_prov) &
                     Q(shipping_to_region_id=t_ctry) &
                     Q(shipping_to_province=t_prov))
                )
            )


        # shipping tax condition:
        #      taxable = True & applies_to = everything
        # sale's tax condition:
        #      (applies_to = everything or sale's category type)
        if shipping_tax:
            query = query & Q(taxable=True) & Q(applies_to_id=None)
        else:
            query = (query &
                     (Q(applies_to_id=None) |
                      Q(applies_to_id=pro_category)))

        if is_business_account:
            query = query & Q(applies_to_business_accounts=True)
        else:
            query = query & Q(applies_to_personal_accounts=True)

        use_after_tax_price = self.get_use_after_tax_price()
        rates = Rate.objects.filter(query).order_by('-apply_after')
        taxes = {}
        taxes_list = []
        for rate in rates:
            tax = {'name': rate.name}
            amount = price

            if rate.apply_after:
                pre_tax = taxes[rate.apply_after]
                amount = pre_tax['amount'] + pre_tax['tax']
            if use_after_tax_price:
                tax['amount'] = to_round(amount / (1 + rate.rate / 100.0))
                tax['tax'] = amount - tax['amount']
            else:
                tax['amount'] = amount
                tax['tax'] = to_round(amount * (1 + rate.rate / 100.0)) - amount

            tax['rate'] = rate.rate
            tax['to_worldwide'] = rate.shipping_to_region_id is None
            tax['show'] = rate.display_on_front is True
            taxes[rate.id] = tax
            taxes_list.append(tax)

        return taxes_list

    def get_shipping(self,
                     handling_fee, shipping_fee,
                     id_carrier, id_service,
                     from_address, to_address,
                     is_business_account):
        shipping = {}
        if id_carrier and int(id_carrier) and id_service and int(id_service):
            service = Service.objects.get(pk=id_service)
            shipping['postage'] = service
            shipping['desc'] = service.desc
            if long(id_carrier):
                carrier = Carrier.objects.get(pk=id_carrier)
                shipping['desc'] = ' - '.join([carrier.desc, service.desc])
        fee = 0.0
        if handling_fee:
            shipping['handling_fee'] = handling_fee
            fee += float(handling_fee)
        if shipping_fee:
            shipping['shipping_fee'] = shipping_fee
            fee += float(shipping_fee)

        use_after_tax_price = self.get_use_after_tax_price()
        subtotal = fee
        total_tax = 0.0
        if fee:
            fee_taxes = self.get_tax(fee, None, from_address, to_address,
                                     shipping_tax=True,
                                     is_business_account=is_business_account)
            shipping['taxes'] = fee_taxes
            for tax in fee_taxes:
                if not use_after_tax_price:
                    subtotal += tax['tax']
                total_tax += tax['tax']

        shipping['subtotal'] = subtotal
        return shipping, fee, total_tax

    def get_shipping_period(self, id_brand, id_shop):
        return {'period': self._get_settings("default_shipment_period",
                                             id_brand,
                                             id_shop)}

    def invoice_number(self, id_brand, id_shop):
        iv_num = self._get_settings('starting_invoice_number',
                                    id_brand,
                                    id_shop)
        args = {
            'brand': Brand.objects.get(pk=id_brand),
            'defaults': {"invoice_number": iv_num},
        }
        if id_shop:
            args.update({
                'shop': Shop.objects.get(pk=id_shop),
            })
        else:
            args.update({
                'shop': None,
            })
        iv_num_obj, created = InvoiceNumber.objects.get_or_create(**args)

        if not created:
            iv_num_obj.invoice_number = F('invoice_number') + 1
            iv_num_obj.save()
            iv_num_obj = InvoiceNumber.objects.get(pk=iv_num_obj.id)

        return iv_num_obj.invoice_number

    def _get_settings(self, key, id_brand, id_shop):
        user = None
        shop = None
        if int(id_shop) != 0:
            shop = Shop.objects.get(pk=id_shop)
            user = shop.owner

        if user is None:
            user = UserProfile.objects.filter(
                Q(work_for_id=id_brand) & Q(role=USERS_ROLE.ADMIN))[0].user

        return get_default_setting(key, user, shop)

    def get_payment(self, id_brand, id_shop):
        payment = {
            'period': self._get_settings("default_payment_period",
                                                id_brand,
                                                id_shop),
        }

        # TODO: penalty, instructions info

        return payment

class SuggestView(View):
    def get(self, request, *args, **kwargs):
        like = request.GET.get('like')
        cli = redis_cli(settings.SALES_SIM_REDIS)
        suggests = cli.zrange(str(like),
                              -settings.SALES_SIM_COUNT,
                              -1,
                              withscores=True)
        suggests.reverse()
        sgt_sales = [sgt[0] for sgt in suggests]
        content = gen_encrypt_json_context(
            ujson.dumps(sgt_sales),
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH
        )

        return HttpResponse(content, mimetype='application/json')

@csrf_exempt
def payment_init(request, *args, **kwargs):
    data = decrypt_json_resp(
        request,
        settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
        settings.PRIVATE_KEY_PATH)

    resp = remote_payment_init(data)
    resp = json.loads(resp)

    content = {'pm_init': resp['pm_init'],
               'cookie': resp['cookie']}

    content = json.dumps(content)
    content = gen_encrypt_json_context(
        content ,
        settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
        settings.PRIVATE_KEY_PATH
    )

    return HttpResponse(content, mimetype='application/json')

