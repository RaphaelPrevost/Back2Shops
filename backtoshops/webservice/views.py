from datetime import date
from django.views.generic import View, ListView, DetailView
from accounts.models import Brand
from sales.models import Sale, ProductType, ProductCategory
from shops.models import Shop

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
