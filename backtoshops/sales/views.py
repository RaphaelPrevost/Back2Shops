import ipdb
from datetime import date
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.db.models.aggregates import Sum
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template import loader
from django.template.context import Context
from django.utils.translation import ugettext_lazy as _, ugettext
from django.views.generic.base import View, TemplateResponseMixin
from formwizard.views import SessionWizardView, NamedUrlSessionWizardView
from sorl.thumbnail import get_thumbnail
from attributes.models import BrandAttribute, BrandAttributePreview, CommonAttribute
from barcodes.models import Barcode
from fouillis.views import BOLoginRequiredMixin
from sales.forms import ShopForm, ProductBrandFormModel, ProductForm, StockStepForm, TargetForm,ListSalesForm
from sales.models import Sale, Product, ProductBrand, ProductPicture, STOCK_TYPE_DETAILED, STOCK_TYPE_GLOBAL, ProductCurrency
from shops.models import Shop
from stocks.models import ProductStock
from backtoshops.globalsettings import get_setting

class UploadProductPictureView(View, TemplateResponseMixin):
    template_name = ""

    def post(self, request):
        if request.FILES:
            is_brand_attribute = request.POST.get('is_brand_attribute', False)
            new_media = ProductPicture(picture=request.FILES[u'files[]'])
            new_media.is_brand_attribute = is_brand_attribute
            new_media.save()
            thumb = get_thumbnail(new_media.picture, '40x43')
            t = loader.get_template('_product_preview_thumbnail.html')
            c = Context({ "picture": new_media.picture })
            preview_html = t.render(c)
            to_ret = {'status': 'ok', 'url': new_media.picture.url, 'thumb_url': thumb.url,
                      'pk': new_media.pk, 'preview_html': preview_html}
            return HttpResponse(json.dumps(to_ret), mimetype="application/json")
        raise HttpResponseBadRequest(_("Must have files attached"))

class ProductBrandView(BOLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_ajax_brands.html"

    def post(self, request):
        try:
            form = ProductBrandFormModel(request.POST, request.FILES)
            if form.is_valid():
                self.new_brand = form.save(commit=False)
                self.new_brand.seller = request.user.get_profile().work_for
                self.new_brand.save()
                messages.success(request, _("Brand has been added"))
                self.brands = ProductBrand.objects.filter(seller=request.user.get_profile().work_for)
        except Exception as e:
            self.errors = e
        return self.render_to_response(self.__dict__)

class BrandLogoView(BOLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_brand_preview_thumbnail.html"

    def get(self, request, brand_id=None):
        if brand_id:
            brand = ProductBrand.objects.get(pk=brand_id)
            # bugfix: handle picture field is NULL
            if brand.picture == 'NULL': return HttpResponse(ugettext('There is no brand logo.'))
            self.picture = brand.picture
            return self.render_to_response(self.__dict__)
        return HttpResponseBadRequest()

class ListSalesView(BOLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = 'list.html'
    list_current = True
    
    def set_sales_list(self,request,sales_type=None):
        """
        this is just internal method to make the self.sales queryset.
        """
        if sales_type == "old":
            self.sales = Sale.objects.filter(mother_brand=request.user.get_profile().work_for,
                                             product__valid_to__lt=date.today())
            self.page_title = _("Old sales")
        else:
            self.sales = Sale.objects.filter(mother_brand=request.user.get_profile().work_for,
                                             product__valid_to__gte=date.today())
            self.page_title = _("Current Sales")
        #put extra fields
        self.sales = self.sales.extra(select={'total_sold_stock':'total_stock-total_rest_stock'})
        return

    def get(self, request, sales_type=None):
        self.set_sales_list(request,sales_type)
        self.form = ListSalesForm()
        print self.__dict__
        return self.render_to_response(self.__dict__)
    
    def post(self, request, sales_type=None):
        self.set_sales_list(request, sales_type)
        self.form = ListSalesForm(request.POST)
        if self.form.is_valid():
            order_by1 = self.form.cleaned_data['order_by1']
            order_by2 = self.form.cleaned_data['order_by2']
            self.sales = self.sales.extra(order_by=[order_by1,order_by2])
        return self.render_to_response(self.__dict__)

class DeleteSalesView(BOLoginRequiredMixin, View):
    
    def post(self, request, sale_id):
        try:
            sale = Sale.objects.get(pk=sale_id)
            sale.delete()
        except:
            return HttpResponse(json.dumps({'success': False}), mimetype='text/json')
        return HttpResponse(json.dumps({'success': True}), mimetype='text/json')

class SaleDetails(BOLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_sale_details.html"

    def _get_common_attributes(self, shop_id, ba):
        rows = []
        for common_attribute in self.common_attributes.all():
            if shop_id:
                results = ProductStock.objects.filter(brand_attribute=ba,
                                                      common_attribute=common_attribute,
                                                      sale=self.sale,
                                                      shop=shop_id)\
                                              .annotate(stock_sum=Sum('stock'), rest_stock_sum=Sum('rest_stock'))
            else:
                results = ProductStock.objects.filter(brand_attribute=ba,
                                                      common_attribute=common_attribute,
                                                      sale=self.sale)\
                                              .annotate(stock_sum=Sum('stock'), rest_stock_sum=Sum('rest_stock'))

            rows.append({
                'common_attribute': common_attribute.name,
                'base': results[0].stock_sum if results else 0,
                'to_sell': results[0].rest_stock_sum if results else 0,
                'sold': results[0].stock - results[0].rest_stock_sum if results else 0,
                'stock': results[0].rest_stock_sum if results else 0
            })
            if shop_id:
                self.total_stock += results[0].stock_sum if results else 0
                self.total_rest_stock += results[0].rest_stock_sum if results else 0
        return rows


    def get(self, request, sale_id, shop_id=None):
        self.sale = Sale.objects.get(pk=sale_id)
        self.common_attributes = CommonAttribute.objects.filter(for_type=self.sale.product.type)
        self.stocks_table = []
        self.total_stock = self.sale.total_stock if not shop_id else 0
        self.total_rest_stock = self.sale.total_rest_stock if not shop_id else 0

        if self.sale.product.brand_attributes.all():
            for attribute in self.sale.product.brand_attributes.all():
                table = {}
                table['attribute'] = attribute.name
                table['rows'] = self._get_common_attributes(shop_id, attribute)
                self.stocks_table.append(table)
        else:
            table = {}
            table['attribute'] = None
            table['rows'] = self._get_common_attributes(shop_id, None)
            self.stocks_table.append(table)

        return self.render_to_response(self.__dict__)

class SaleDetailsShop(BOLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_sale_details_shop.html"

    def get(self, request, sale_id=None):
        self.sale = Sale.objects.get(pk=sale_id)
        self.shops = Shop.objects.filter(mother_brand=request.user.get_profile().work_for)\
                                        .filter(productstock__sale=self.sale).distinct()
        return self.render_to_response(self.__dict__)

def add_sale(*args, **kwargs):
    forms = [
        (SaleWizardNew.STEP_SHOP, ShopForm),
        (SaleWizardNew.STEP_PRODUCT, ProductForm),
        (SaleWizardNew.STEP_STOCKS, StockStepForm),
        (SaleWizardNew.STEP_TARGET, TargetForm)
    ]
    
    initial_product = {
        'currency': ProductCurrency.objects.get(code=get_setting('default_currency')),
    }
    
    initials = {
        SaleWizardNew.STEP_PRODUCT: initial_product,
    }

    sale_wizard = login_required(SaleWizardNew.as_view(forms, initial_dict = initials,url_name="add_sale",
                                                       done_step_name="list_sales"),
                                 login_url="login")
    return sale_wizard(*args, **kwargs)

def edit_sale(*args, **kwargs):
    forms = [
        (SaleWizardNew.STEP_SHOP, ShopForm),
        (SaleWizardNew.STEP_PRODUCT, ProductForm),
        (SaleWizardNew.STEP_STOCKS, StockStepForm),
        (SaleWizardNew.STEP_TARGET, TargetForm)
    ]

    if not 'sale_id' in kwargs:
        return add_sale(*args, **kwargs)
    sale_id = kwargs['sale_id']
    sale = Sale.objects.get(pk=sale_id)

    # We use pk in initials so we can use has_changed() method on forms
    initial_shop = {
        'target_market': sale.type_stock,
        'shops': [ s.pk for s in sale.shops.all() ]
    }

    pictures = []
    for pic in sale.product.pictures.exclude(is_brand_attribute=True):
        pictures.append({
            'pk': pic.pk,
            'url': pic.picture.url,
            'thumb_url': get_thumbnail(pic.picture, '40x43').url
        })
    brand_attributes = []
    for i in sale.product.brand_attributes.all():
        bap = BrandAttributePreview.objects.get(brand_attribute=i, product=sale.product)
        brand_attributes.append({
            'name': i.name,
            'ba_id': i.pk,
            'texture': get_thumbnail(i.texture, "15x15").url if i.texture else None,
            'preview': get_thumbnail(bap.preview.picture, "39x43").url if bap.preview else None,
            'preview_pk': bap.preview.pk if bap.preview else None
        })

    initial_product = {
        'brand': sale.product.brand.pk,
        'type': sale.product.type.pk,
        'category': sale.product.category.pk,
        'name': sale.product.name,
        'description': sale.product.description,
        'valid_from': sale.product.valid_from,
        'valid_to': sale.product.valid_to,
        'normal_price': sale.product.normal_price,
        'currency': sale.product.currency,
        'discount': sale.product.discount,
        'discount_price': sale.product.discount_price,
        'discount_type': sale.product.discount_type,
        'brand_attributes': brand_attributes,
        'pictures': pictures
    }

    initial_stocks = []
    for i in ProductStock.objects.filter(sale=sale):
        initial_stocks.append({
            'brand_attribute': i.brand_attribute.pk if i.brand_attribute else None,
            'common_attribute': i.common_attribute.pk,
            'shop': i.shop.pk if i.shop else None,
            'stock': i.stock
        })

    initial_barcodes = []
    for i in Barcode.objects.filter(sale=sale):
        initial_barcodes.append({
            'brand_attribute': i.brand_attribute.pk if i.brand_attribute else None,
            'common_attribute': i.common_attribute.pk,
            'upc': i.upc
        })

    initial_stocks_step = {
        'stocks_initials': initial_stocks,
        'barcodes_initials': initial_barcodes
    }

    initial_target = {
        'gender': sale.gender
    }

    initials = {
        SaleWizardNew.STEP_SHOP: initial_shop,
        SaleWizardNew.STEP_PRODUCT: initial_product,
        SaleWizardNew.STEP_STOCKS: initial_stocks_step,
        SaleWizardNew.STEP_TARGET: initial_target
    }

    settings = {
        'base_template': 'edit_sale_base.html',
        'edit_mode': True,
        'sale': sale
    }
    sale_wizard = login_required(SaleWizardNew.as_view(forms, initial_dict=initials,
                                                       url_name="edit_sale",
                                                       done_step_name="list_sales",
                                                       **settings),
                                 login_url="login")

    return sale_wizard(*args, **kwargs)

class StocksInfos(object):
    def __init__(self):
        self.__dict__['stocks_expired'] = False
        self.__dict__['barcodes_expired'] = False
        self.__dict__['shops'] = None
        self.__dict__['product_type'] = None
        self.__dict__['brand_attributes'] = None
        self.__dict__['stocks'] = None
        self.__dict__['barcodes'] = None
        self.__dict__['last_stocks_initials'] = None
        self.__dict__['last_barcodes_initials'] = None

    def __setattr__(self, key, value):
        if key != 'stocks' and key != 'barcodes':
            if self.__dict__.get(key, None) != None:
                if self.__dict__[key] != value:
                    if key in ['shops', 'product_type', 'brand_attributes']:
                        self.__dict__['stocks_expired'] = True
                    if key in ['product_type', 'brand_attributes']:
                        self.__dict__['barcodes_expired'] = True
            else:
                if value:
                    if key in ['shops', 'product_type', 'brand_attributes']:
                        self.__dict__['stocks_expired'] = True
                    if key in ['product_type', 'brand_attributes']:
                        self.__dict__['barcodes_expired'] = True
        self.__dict__[key] = value

class SaleWizardNew(SessionWizardView, NamedUrlSessionWizardView):
    STEP_SHOP = 'shop'
    STEP_PRODUCT = 'product'
    STEP_STOCKS = 'stocks'
    STEP_TARGET = 'target'
    file_storage = FileSystemStorage()
    base_template = "add_sale_base.html"
    edit_mode = False
    sale = None
    stock_form = None

    @transaction.commit_on_success
    def done(self, form_list, **kwargs):
        if self.edit_mode:
            sale = self.sale
            product = sale.product
        else:
            sale = Sale()
            product = Product()
            sale.product = product
        sale.mother_brand = self.request.user.get_profile().work_for
        sale.type_stock = form_list[0].cleaned_data['target_market']
        sale.save()
        if sale.type_stock == STOCK_TYPE_DETAILED:
            sale.shops = form_list[0].cleaned_data['shops']
        product_form = form_list[1].cleaned_data
        product.sale = sale
        product.brand = product_form['brand']
        product.type = product_form['type']
        product.category = product_form['category']
        product.name = product_form['name']
        product.description = product_form['description']
        product.valid_from = product_form['valid_from']
        product.valid_to = product_form['valid_to']
        product.normal_price = product_form['normal_price']
        product.currency = product_form['currency']
        product.discount = product_form['discount']
        product.discount_price = product_form['discount_price']
        product.discount_type = product_form['discount_type']
        product.save()

        brand_attributes = form_list[1].brand_attributes
        ba_pks = []
        for ba in brand_attributes.cleaned_data:
            if not ba['DELETE']:
                preview=None
                if ba['preview_pk']:
                    preview=ProductPicture.objects.get(pk=ba['preview_pk'])
                (bap, created) = BrandAttributePreview.objects.get_or_create(
                    brand_attribute=BrandAttribute.objects.get(pk=ba['ba_id']),
                    product=product,
                    preview=preview
                )
                bap.save()
                ba_pks.append(ba['ba_id'])

        pictures = form_list[1].pictures
        pp_pks = [int(pp['pk']) for pp in pictures.cleaned_data if not pp['DELETE']]
        product.pictures = ProductPicture.objects.filter(pk__in=pp_pks)
        product.save()

        stock_step = form_list[2]
        total_stock = 0
        for i in stock_step.stocks:
            if i.is_valid() and i.cleaned_data and i.cleaned_data['stock']:
                stock = ProductStock()
                stock.sale = sale
                stock.stock = stock.rest_stock = i.cleaned_data['stock']
                stock.shop = None
                if i.cleaned_data['shop']:
                    stock.shop = Shop.objects.get(pk=i.cleaned_data['shop'])
                stock.common_attribute = CommonAttribute.objects.get(pk=i.cleaned_data['common_attribute'])
                ba_pk = i.cleaned_data['brand_attribute']
                stock.brand_attribute = BrandAttribute.objects.get(pk=ba_pk) if ba_pk else None
                total_stock += stock.stock
                stock.save()
        sale.total_rest_stock = sale.total_stock = total_stock

        for i in stock_step.barcodes:
            if i.is_valid() and i.cleaned_data and i.cleaned_data['upc']:
                barcode = Barcode()
                barcode.sale = sale
                barcode.upc = i.cleaned_data['upc']
                barcode.common_attribute = CommonAttribute.objects.get(pk=i.cleaned_data['common_attribute'])
                ba_pk = i.cleaned_data['brand_attribute']
                barcode.brand_attribute = BrandAttribute.objects.get(pk=ba_pk) if ba_pk else None
                barcode.save()

        if self.edit_mode:
            # Let's check if there is orphan stocks, if there is delete them
            for i in ProductStock.objects.filter(sale=sale):
                if i.brand_attribute and i.brand_attribute.pk not in ba_pks:
                    i.delete()

        target = form_list[3].cleaned_data
        sale.gender = target['gender']
        sale.complete = True
        sale.save()

        if self.request.session.get('stocks_infos', None):
            del(self.request.session['stocks_infos'])

        return redirect("list_sales")

    def dispatch(self, request, *args, **kwargs):
        self.stocks_infos = request.session.get('stocks_infos', StocksInfos())
        return super(SaleWizardNew, self).dispatch(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Override post to catch cancel actions, else just call super
        """
        wizard_cancel = self.request.POST.get('wizard_cancel', None)
        if wizard_cancel:
            self.storage.reset()
            if self.request.session.get('stocks_infos', None):
                del(self.request.session['stocks_infos'])

            return redirect('/')
        if self.edit_mode:
            prev_step = self.request.POST.get('wizard_prev_step', None)
            if prev_step and prev_step in self.get_form_list():
                self.storage.current_step = prev_step
                return redirect(self.url_name, step=prev_step, sale_id=self.sale.pk)

        return super(SaleWizardNew, self).post(*args, **kwargs)

    def process_step(self, form):
        if self.steps.current == self.STEP_SHOP:
            self.stocks_infos.shops = form.cleaned_data
        elif self.steps.current == self.STEP_PRODUCT:
            self.stocks_infos.product_type = form.cleaned_data['type']
            self.stocks_infos.brand_attributes = form.brand_attributes.cleaned_data
        elif self.steps.current == self.STEP_STOCKS:
            self.stocks_infos.stocks = form.stocks.cleaned_data
            #self.stocks_infos.stocks_expired = True
            self.stocks_infos.barcodes = form.barcodes.cleaned_data
            #self.stocks_infos.barcodes_expired = True
        if self.stocks_infos.stocks_expired or self.stocks_infos.barcodes_expired:
            self.storage.set_step_data(self.STEP_STOCKS, None)
            self.storage.set_step_files(self.STEP_STOCKS, None)
        return super(SaleWizardNew, self).process_step(form)


    def render(self, form=None, **kwargs):
#        if self.request.session.get("edit_mode", False):
#            self.base_template = "edit_sale_base.html"
        self.template_name = "add_sale_"+str(self.steps.current)+".html"
        form = form or self.get_form()
        context = self.get_context_data(form, **kwargs)
        self.request.session['stocks_infos'] = self.stocks_infos
        return self.render_to_response(context)

    def render_next_step(self, form, **kwargs):
        if self.edit_mode:
            next_step = self.get_next_step()
            self.storage.current_step = next_step
            return redirect(self.url_name, step=next_step, sale_id=self.sale.pk)
        return super(SaleWizardNew, self).render_next_step(form, **kwargs)

    def render_revalidation_failure(self, failed_step, form, **kwargs):
        if self.edit_mode:
            self.storage.current_step = failed_step
            return redirect(self.url_name, step=failed_step, sale_id=self.sale.pk)
        return super(SaleWizardNew, self).render_revalidation_failure(failed_step, form, **kwargs)

    def render_done(self, form, **kwargs):
        if self.edit_mode:
            if kwargs.get('step', None) != self.done_step_name:
                return redirect(self.url_name, step=self.done_step_name, sale_id=self.sale.pk)
        return super(SaleWizardNew, self).render_done(form, **kwargs)

    def _render_preview(self, step):
        context = {
            'context': self.get_form(step, self.storage.get_step_data(step), self.storage.get_step_files(step))
        }
        if step == self.STEP_PRODUCT:
            if context['context'].is_valid():
                pictures = None
                if len(context['context'].pictures.cleaned_data) > 0:
                    pictures = ProductPicture.objects.get(pk=context['context'].pictures.cleaned_data[0]['pk'])
                context.update({
                    'brand_object': ProductBrand.objects.get(pk=context['context'].cleaned_data['brand'].pk),
                    'product_picture': pictures,
                })
        t = loader.get_template("add_sale_preview_"+step+".html")
        c = Context(context)
        return t.render(c)

    def get_context_data(self, form, *args, **kwargs):
        context = super(SaleWizardNew, self).get_context_data(form, *args, **kwargs)
        if self.edit_mode:
            context.update({
                'sale_id': self.sale.pk
            })
        context.update({
            'request': self.request,
            'base_template': self.base_template
        })
        if self.steps.current == self.STEP_SHOP:
            context.update({
                'form_title': _("Shops Definition"),
                'preview_shop': "blank"
            })
        elif self.steps.current == self.STEP_PRODUCT:
            product_picture = None
            if self.edit_mode:
                if self.sale.product.pictures.count() > 0:
                    product_picture = self.sale.product.pictures.all()[0]
            else:
                if form.pictures.is_valid():
                    if len(form.pictures.cleaned_data) > 0:
                        product_picture = ProductPicture.objects.get(pk=form.pictures.cleaned_data[0]['pk'])
            context.update({
                'form_title': _("Product Definition"),
                'preview_shop': self._render_preview(self.STEP_SHOP),
                'preview_product': "blank",
                'product_picture': product_picture,
                'product_brand_form': ProductBrandFormModel
            })
        elif self.steps.current == self.STEP_STOCKS:
            context.update({
                'form_title': _("Stocks Definition"),
                'attributes': self.brand_attributes,
                'preview_shop': self._render_preview(self.STEP_SHOP),
                'preview_product': self._render_preview(self.STEP_PRODUCT),
                'common_attributes': self.common_attributes,
                'shops': self.shops,
                'global_stock': True if self.target_market == "N" else False
            })
        elif self.steps.current == self.STEP_TARGET:
            context.update({
                'form_title': _("Target Definition"),
                'preview_shop': self._render_preview(self.STEP_SHOP),
                'preview_product': self._render_preview(self.STEP_PRODUCT),
                'preview_target': "blank",
            })
        return context

    def get_form_kwargs(self, step=None):
        if step == self.STEP_SHOP or step == self.STEP_PRODUCT:
            return {'mother_brand': self.request.user.get_profile().work_for}
        return super(SaleWizardNew, self).get_form_kwargs(step)

    def _get_stock(self, ba, ca, ps):
        if self.edit_mode:
            for i in self.initial_dict.get(self.STEP_STOCKS).get('stocks_initials', None):
                if i['brand_attribute'] == ba:
                    if i['common_attribute'] == ca:
                        if i['shop'] == ps:
                            return i['stock']
        else:
            if self.stocks_infos.stocks:
                for i in self.stocks_infos.stocks:
                    if i:
                        if i['brand_attribute'] == ba:
                            if i['common_attribute'] == ca:
                                if i['shop'] == ps:
                                    return i['stock']
        return None

    def _get_barcode(self, ba, ca):
        if self.edit_mode:
            for i in self.initial_dict.get(self.STEP_STOCKS).get('barcodes_initials', None):
                if i['brand_attribute'] == ba:
                    if i['common_attribute'] == ca:
                        return i['upc']
        else:
            if self.stocks_infos.barcodes:
                for i in self.stocks_infos.barcodes:
                    if i:
                        if i['brand_attribute'] == ba:
                            if i['common_attribute'] == ca:
                                return i['upc']
        return None

    def _get_stock_initial(self, ba, ca, sh, st):
        return {
            'brand_attribute': ba,
            'common_attribute': ca,
            'shop': sh,
            'stock': st,
        }

    def get_form_initial(self, step):
        if step == None:
            step = self.steps.current
        if step == self.STEP_STOCKS:
            shop_obj = self.get_form(self.STEP_SHOP, data=self.storage.get_step_data(self.STEP_SHOP))
            product_obj = self.get_form(self.STEP_PRODUCT,
                data=self.storage.get_step_data(self.STEP_PRODUCT),
                files=self.storage.get_step_files(self.STEP_PRODUCT)
            )
            if not shop_obj.is_valid() or not product_obj.is_valid() or not product_obj.brand_attributes.is_valid():
                return {}
            self.common_attributes = CommonAttribute.objects.filter(for_type=product_obj.cleaned_data['type'])
            brand_attributes = [ba['ba_id'] for ba in product_obj.brand_attributes.cleaned_data if not ba['DELETE']]
            self.brand_attributes = BrandAttribute.objects.filter(pk__in=brand_attributes)
            self.shops = shop_obj.cleaned_data['shops'] or None
            self.target_market = shop_obj.cleaned_data['target_market']

            toret = {}
            # if self.stocks_infos.stocks_expired:
            # Initializes the initials for stocks form
            initials = []
            if shop_obj.cleaned_data['target_market'] == STOCK_TYPE_GLOBAL: #National market
                if self.brand_attributes:
                    for ba in self.brand_attributes:
                        for ca in self.common_attributes:
                            initials.append(self._get_stock_initial(ba.pk, ca.pk, None, self._get_stock(ba.pk, ca.pk, None)))
                else:
                    for ca in self.common_attributes:
                        initials.append(self._get_stock_initial(None, ca.pk, None, self._get_stock(None, ca.pk, None)))

            else:
                if self.brand_attributes:
                    for shop in self.shops:
                        for ba in self.brand_attributes:
                            for ca in self.common_attributes:
                                initials.append(self._get_stock_initial(ba.pk, ca.pk, shop.pk, self._get_stock(ba.pk, ca.pk, shop.pk)))
                else:
                    for shop in self.shops:
                        for ca in self.common_attributes:
                            initials.append(self._get_stock_initial(None, ca.pk, shop.pk, self._get_stock(None, ca.pk, shop.pk)))

            self.stocks_infos.stocks_expired = False
            self.stocks_infos.last_stocks_initials = {'stocks_initials': initials}
            toret.update({'stocks_initials': initials})
            # else:
            #     toret.update(self.stocks_infos.last_stocks_initials)

            # if self.stocks_infos.barcodes_expired:
            # Initializes the initials for barcodes form
            initials = []
            if self.brand_attributes:
                for ba in self.brand_attributes:
                    for ca in self.common_attributes:
                        initials.append({
                            'brand_attribute': ba.pk,
                            'common_attribute': ca.pk,
                            'upc': self._get_barcode(ba.pk, ca.pk),
                        })
            else:
                for ca in self.common_attributes:
                    initials.append({
                        'brand_attribute': None,
                        'common_attribute': ca.pk,
                        'upc': self._get_barcode(None, ca.pk),
                    })

            self.stocks_infos.barcodes_expired = False
            self.stocks_infos.last_barcodes_initials = {'barcodes_initials': initials}
            toret.update({'barcodes_initials': initials})
            # else:
            #     toret.update(self.stocks_infos.last_barcodes_initials)
            return toret
        return super(SaleWizardNew, self).get_form_initial(step)
