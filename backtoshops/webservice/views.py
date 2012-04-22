import json
import base64
import math
from datetime import date
from django.contrib.auth import authenticate as _authenticate
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import View, ListView, DetailView
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from accounts.models import Brand
from sales.models import Sale, ProductType, ProductCategory, STOCK_TYPE_DETAILED, STOCK_TYPE_GLOBAL,ShopsInSale
from shops.models import Shop
from barcodes.models import Barcode
from brandings.models import Branding
from datetime import datetime
import settings

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
        queryset = Sale.objects.filter(product__valid_from__lte=date.today()).filter(product__valid_to__gte=date.today())
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

#
# APIs for managing shop inventory
#

def basic_auth(func):
	"""Decorator for basic auth"""
	def wrapper(request, *args, **kwargs):
		try:
			if is_authenticated(request):
				return func(request, *args, **kwargs)
		except Exception, ex:
			return HttpResponse(json.dumps({'success': False, 'error': ex.message}), mimetype='text/json')
	return wrapper
	
def is_authenticated(request):
    token = request.META['HTTP_AUTHORIZATION'].replace('Basic ', '')
    username, password = base64.decodestring(token).split(':')
    user = _authenticate(username=username, password=password)
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
        queryset = Sale.objects.filter(product__valid_from__lte=date.today()).filter(product__valid_to__gte=date.today())
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
