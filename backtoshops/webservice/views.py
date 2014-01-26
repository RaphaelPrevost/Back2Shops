import base64
import json
import math
import settings
from collections import defaultdict
from datetime import date
from datetime import datetime

from django.contrib.auth import authenticate as _authenticate
from django.db.models import Max
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import View, ListView, DetailView
from django.views.decorators.csrf import csrf_exempt

from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.constant import SERVICES

from attributes.models import BrandAttributePreview
from attributes.models import CommonAttribute
from accounts.models import Brand
from barcodes.models import Barcode
from brandings.models import Branding
from common.filter_utils import get_filter, get_order_by
from common.error import InvalidRequestError
from common.error import ParamsValidCheckError
from common.fees import compute_fee
from sales.models import ProductCategory
from sales.models import ProductType
from sales.models import STOCK_TYPE_GLOBAL
from sales.models import Sale
from sales.models import ShopsInSale
from sales.models import TypeAttributeWeight
from shippings.models import CustomShippingRateInShipping
from shippings.models import SC_CARRIER_SHIPPING_RATE
from shippings.models import SC_CUSTOM_SHIPPING_RATE
from shippings.models import SC_FLAT_RATE
from shippings.models import FlatRateInShipping
from shippings.models import ServiceInShipping
from shippings.models import Carrier, Service
from shops.models import Shop
from taxes.models import Rate

fail = lambda s: HttpResponse(json.dumps({'success': False, 'error': s}), mimetype='text/json')

class BaseWebservice(View):
    def render_to_response(self, context, **response_kwargs):
        response_kwargs.update({
            'mimetype': 'text/xml'
        })
        return super(BaseWebservice, self).render_to_response(context, **response_kwargs)

    def get_context_data(self,**kwargs):
        kwargs.update({"settings":settings, })
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
        brand = self.request.GET.get('seller', None)
        queryset = ProductType.objects.all()
        self.q_category = ProductCategory.objects.all()
        if brand:
            queryset = queryset.filter(products__sale__mother_brand=brand).distinct()
            self.q_category = self.q_category.filter(products__sale__mother_brand=brand).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        kwargs.update({
            'categories': self.q_category
        })
        return kwargs


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
    queryset = Branding.objects.exclude(show_from__gt=datetime.now()).exclude(show_until__lt=datetime.now()).order_by('sort_key')[:5]

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
                Q(product__name__contains=search)|
                Q(product__description__contains=search)|
                Q(mother_brand__name__contains=search)|
                Q(product__type__name__contains=search)|
                Q(product__brand_attributes__name__contains=search)).distinct()

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
        barcodes = Barcode.objects.filter(upc=item)
        shop = Shop.objects.get(upc=shop_upc)
        sales = Sale.objects.filter(barcodes__in=barcodes, shops__in=[shop])
        if sales.count() > 0:
            return sales[0]
        return None
    except Exception, ex:
        return None

def stock_setter(request,val):
    token = request.META['HTTP_AUTHORIZATION'].replace('Basic ', '')
    username, password = base64.decodestring(token).split(':')
    user = _authenticate(username=username, password=password)

    try:
        shop_upc = request.REQUEST['shop']
        shop = Shop.objects.get(upc=shop_upc)
    except:
        return fail('shop upc must be given')

    sale = get_sale(shop_upc, request.REQUEST['item'])

    if sale is None:
        return fail('sale not found with given shop and item')

    #if shop is frozen.
    try:
        if ShopsInSale.objects.get(shop=shop,sale=sale).is_freezed:
            return fail("this shop is frozen, can't update stocks")
    except:
         return fail('shop is not found in this sale')

    if sale.type_stock == STOCK_TYPE_GLOBAL: #stocks at global level
        pass
    else: #stocks at shops level
        if user.is_staff or shop in user.get_profile().shops.all(): # can update
            try:
                stock = sale.detailed_stock.get(shop=shop)
                stock.rest_stock += val
                if stock.rest_stock < 0:
                    stock.rest_stock = 0
                if stock.stock < stock.rest_stock:
                    stock.stock = stock.rest_stock
                stock.save()
            except:
                return fail('stock of the given shop is invalid.')
        else: #this operator can't touch this shop.
            return fail('no access to this shop''s stock')

    sale.total_rest_stock += val
    if sale.total_rest_stock < 0:
        sale.total_rest_stock = 0
    if sale.total_stock < sale.total_rest_stock:
        sale.total_stock = sale.total_rest_stock
    sale.save()
    return HttpResponse(json.dumps({'success': True, 'total_stock': sale.total_stock, 'total_rest_stock': sale.total_rest_stock}), mimetype='text/json')

@csrf_exempt
@basic_auth
def barcode_increment(request):
    return stock_setter(request, 1)

@csrf_exempt
@basic_auth
def barcode_decrement(request):
    return stock_setter(request, -1)

@csrf_exempt
@basic_auth
def barcode_returned(request):
    return stock_setter(request, 1)


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

class BaseCryptoWebService(BaseWebservice):
    from_ = SERVICES.USR
    def render_to_response(self, context, **response_kwargs):
        resp = super(BaseCryptoWebService, self).render_to_response(context, **response_kwargs)
        debugging = self.request.GET.get('debugging', False)
        if settings.CRYPTO_RESP_DEBUGING and debugging:
            return resp
        resp.render()
        if self.request.method == 'GET':
            self.from_ = self.request.GET.get('from', SERVICES.USR)
        elif self.request.method == 'POST':
            self.from_ = self.request.POST.get('from', SERVICES.USR)
        content = gen_encrypt_json_context(
            resp.content,
            settings.SERVER_APIKEY_URI_MAP[self.from_],
            settings.PRIVATE_KEY_PATH)
        response_kwargs.update({
            'mimetype': 'application/json'
        })

        return HttpResponse(content, **response_kwargs)

class TaxesListView(BaseCryptoWebService, ListView):
    template_name = "taxes_list.xml"

    def get_queryset(self):
        fromCountry = self.request.GET.get('fromCountry', None)
        fromProvince = self.request.GET.get('fromProvince', None)
        toCountry = self.request.GET.get('toCountry', None)
        toProvince = self.request.GET.get('toProvince', None)

        if fromCountry is None or toCountry is None:
            return []

        queryset = Rate.objects.filter(
            region_id=fromCountry
        ).filter(
            shipping_to_region_id=toCountry
        )
        if fromProvince:
            queryset = queryset.filter(province=fromProvince)
        if toProvince:
            queryset = queryset.filter(province=toProvince)

        return queryset

    def get_context_data(self, **kwargs):
        fromCountry = self.request.GET.get('fromCountry', None)
        fromProvince = self.request.GET.get('fromProvince', None)
        kwargs.update({'country': fromCountry})
        if fromProvince:
            kwargs.update({'province': fromProvince})
        return kwargs


def populate_carriers(carrier_services=None, shipping=None):
    """
    """
    if carrier_services:
        carrier_services = dict(carrier_services)
    else:
        carrier_services = defaultdict(list)
    carrier_services.pop(0, None)
    if shipping:
        services_in_shipping = ServiceInShipping.objects.filter(
            shipping=shipping)
        for item in services_in_shipping:
            carrier_services[item.service.carrier.pk].append(item.service.pk)

    if not carrier_services:
        raise ParamsValidCheckError("invalid_shipping_or_carrier_services: "
                                    "shipping-%s, carrier_services-%s"
                                    % shipping, carrier_services)
    carriers = Carrier.objects.filter(pk__in=carrier_services.keys())
    for carrier in carriers:
        kwargs = {'carrier': carrier}
        services_id = carrier_services.get(carrier.pk)
        if services_id:
            kwargs['pk__in'] = services_id
        services = Service.objects.filter(**kwargs)
        setattr(carrier, 'carrier_services', services)

    return carriers

def get_custom_rules(custom_rules=None, shipping=None):
    kwargs = defaultdict()
    if shipping:
        kwargs['shipping'] = shipping
    if custom_rules:
        kwargs['pk__in'] = custom_rules

    rules_in_shipping = CustomShippingRateInShipping.objects.filter(**kwargs)
    return [item.custom_shipping_rate for item in rules_in_shipping]

class ShippingInfoView(BaseCryptoWebService, ListView):
    template_name = "shipping_info.xml"

    def get_queryset(self):
        sale_id = self.request.GET.get('sale', None)
        sales_id = self.request.GET.get('sales', None)
        if sale_id:
            sales_id = [int(sale_id)]
        else:
            sales_id = json.loads(sales_id)
        if not sales_id:
            raise InvalidRequestError(
                "invalid_shipping_info_request_Miss_param: %s"
                % self.request.GET)

        queryset = Sale.objects.filter(pk__in=sales_id)
        for object in queryset:
            self._populate_type_attrs(object)
            self._populate_brand_attrs(object)
            self._populate_type_attrs_weight(object)
            self._populate_shipping_rate(object)

        return queryset

    def _populate_type_attrs(self, sale):
        """ populate type attributes info for this sale item.
        """
        tp_attrs = CommonAttribute.objects.filter(
            for_type=sale.product.type)
        setattr(sale, 'type_attributes', tp_attrs)
        return sale

    def _populate_brand_attrs(self, sale):
        """ populate brand attributes info for this sale item.
        """
        br_attrs_prevs = BrandAttributePreview.objects.filter(
            product=sale.product)
        br_attrs = [br_prev.brand_attribute for br_prev in br_attrs_prevs]
        setattr(sale, 'brand_attributes', br_attrs)
        return sale

    def _populate_type_attrs_weight(self, sale):
        attrs_weight = TypeAttributeWeight.objects.filter(sale=sale)
        if attrs_weight:
            setattr(sale,
                    'attributes_weight',
                    attrs_weight)

    def _populate_shipping_rate(self, sale):
        """ populate carrier/custom/flat shipping rate
        """
        sp_calc_method = sale.shippinginsale.shipping.shipping_calculation
        shipping = sale.shippinginsale.shipping
        if sp_calc_method == SC_CARRIER_SHIPPING_RATE:
            carriers = populate_carriers(shipping=shipping)
            setattr(sale, 'carriers', carriers)

        elif sp_calc_method == SC_CUSTOM_SHIPPING_RATE:
            custom_rules = get_custom_rules(shipping=shipping)
            setattr(sale, 'custom_rules', custom_rules)

        elif sp_calc_method == SC_FLAT_RATE:
            ft_in_shipping = FlatRateInShipping.objects.get(shipping=shipping)
            setattr(sale,
                    'flat_rate',
                    ft_in_shipping.flat_rate)
        return sale


class ShippingFeesView(BaseCryptoWebService, ListView):
    template_name = "shipping_fees.xml"

    def get_context_data(self, **kwargs):
        carriers, custom_rules = kwargs.get('object_list') or ([], [])
        kwargs['carriers'] = carriers
        kwargs['custom_rules'] = custom_rules
        return kwargs

    def get_queryset(self):
        carrier_services = self.request.GET.get('carrier_services', None)
        weight = self.request.GET.get('weight')
        weight_unit = self.request.GET.get('unit')
        dest = self.request.GET.get('dest')
        orig = self.request.GET.get('orig')

        if carrier_services:
            carrier_services = json.loads(carrier_services)

        if (weight is None or
            weight_unit is None or
            dest is None or
            not carrier_services):
            raise InvalidRequestError(
                "invalide_shipping_fees_request_miss_params %s"
                % self.request.GET)

        # carrier id is 0 for custom rules.
        rules = [item[1] for item in carrier_services
                         if item[0] == 0]
        carriers = populate_carriers(carrier_services)
        custom_rules = get_custom_rules(custom_rules=rules)

        # calculate fees for services.
        for carrier in carriers:
            for service in carrier.carrier_services:
                data = {'carrier': carrier.pk,
                        'addr_orig': orig,
                        'addr_dest': dest,
                        'service': service.pk,
                        'weight': weight,
                        'weight_unit': weight_unit}
                fee = compute_fee(data)
                setattr(service, 'shipping_fee', fee)

        return [carriers, custom_rules]


