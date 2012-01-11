import json
import base64
from datetime import date
from django.contrib.auth import authenticate as _authenticate
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import View, ListView, DetailView
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from accounts.models import Brand
from sales.models import Sale, ProductType, ProductCategory
from shops.models import Shop
from barcodes.models import Barcode

class BaseWebservice(View):
    def render_to_response(self, context, **response_kwargs):
        response_kwargs.update({
            'mimetype': 'text/xml'
        })
        return super(BaseWebservice, self).render_to_response(context, **response_kwargs)

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
			print ex
		return HttpResponseForbidden()
	return wrapper
	
def is_authenticated(request):
	token = request.META['HTTP_AUTHORIZATION'].replace('Basic ', '')
	username, password = base64.decodestring(token).split(':')
	user = _authenticate(username=username, password=password)
	shop = Shop.objects.get(upc=request.REQUEST['shop'])
	return (shop.mother_brand.employee.filter(user__id=user.id).count() > 0)

@csrf_exempt
def authenticate(request):
	if is_authenticated(request):
		return HttpResponse(json.dumps({'success': True}), mimetype='text/json')
	else:
		return HttpResponseForbidden()

def get_sale(shop, item):
	try:
		shop = Shop.objects.get(upc=shop)
		barcodes = Barcode.objects.filter(upc=item)
		sales = Sale.objects.filter(barcodes__in=barcodes, shops__in=[shop])
		if sales.count() > 0:
			return sales[0]
		return None
	except Exception, ex:
		return None

@basic_auth
@csrf_exempt
def barcode_increment(request):
	sale = get_sale(request.REQUEST['shop'], request.REQUEST['item'])
	if sale is not None:
		sale.total_stock += 1
		sale.save()
		return HttpResponse(json.dumps({'success': True, 'total_stock': sale.total_stock}), mimetype='text/json')
	return HttpResponse(json.dumps({'success': False, 'error': 'Barcode Error'}), mimetype='text/json')

@basic_auth
@csrf_exempt
def barcode_decrement(request):
	sale = get_sale(request.REQUEST['shop'], request.REQUEST['item'])
	if sale is not None:
		sale.total_stock -= 1
		if sale.total_stock > 0:
			sale.save()
		return HttpResponse(json.dumps({'success': True, 'total_stock': sale.total_stock}), mimetype='text/json')	
	return HttpResponse(json.dumps({'success': False, 'error': 'Barcode Error'}), mimetype='text/json')

@basic_auth
@csrf_exempt
def barcode_returned(request):		
	sale = get_sale(request.REQUEST['shop'], request.REQUEST['item'])
	if sale is not None:
		sale.total_stock += 1
		return HttpResponse(json.dumps({'success': True, 'total_stock': sale.total_stock}), mimetype='text/json')
	return HttpResponse(json.dumps({'success': False, 'error': 'Barcode Error'}), mimetype='text/json')
