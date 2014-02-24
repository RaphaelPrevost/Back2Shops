import logging
import settings
import ujson

from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext_lazy
from django.views.generic.base import View, TemplateResponseMixin
from django.views.generic.edit import CreateView, UpdateView
from fouillis.views import LoginRequiredMixin

from common.error import UsersServerError
from common.fees import compute_fee
from common.orders import get_order_detail
from common.orders import get_order_list
from common.orders import send_shipping_fee
from orders.forms import ListOrdersForm
from orders.forms import ShippingForm
from orders.models import Shipping
from sales.models import Sale



def is_decimal(val):
    try:
        Decimal(val)
    except ValueError:
        return False
    return True

class ShippingFee(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        fee = compute_fee(request.GET)
        return HttpResponse(ujson.dumps(fee), mimetype="application/json")

class BaseShippingView(LoginRequiredMixin):
    template_name = "shipping_fee.html"
    form_class = ShippingForm
    model = Shipping

    def get_success_url(self):
        return reverse("shipment_status")

    def get_context_data(self, **kwargs):
        kwargs.update({
            'shipping_pk': self.kwargs.get('pk', None),
            'request': self.request,
            })
        return kwargs

    def _send_shipping_fee(self, request):
        id_shipment = request.POST.get('shipment')
        id_postage = request.POST.get('service')
        shipping_fee = request.POST.get('total_fee')
        try:
            assert is_decimal(id_shipment), 'shipment: %s should be a digit' % id_shipment
            assert is_decimal(id_postage), 'service: %s should be a digit' % id_postage
            assert is_decimal(shipping_fee), 'shipping fee: %s should be a digit' % shipping_fee
        except AssertionError, e:
            logging.error('send_shipping_fee args error: %s' % e,
                          exc_info=True)
            raise
        send_shipping_fee(id_shipment, id_postage, shipping_fee)

    def _compute_total_fee(self, request):
        total_fee = compute_fee(request.POST)
        request.POST.update({'total_fee': total_fee})
        return total_fee


class CreateShippingView(BaseShippingView, CreateView):
    def get_initial(self):
        initial = {"addr_orig": self.request.GET.get('addr_orig', 'orignal'),
                   "addr_dest": self.request.GET.get('addr_dest', 'dest'),
                   "shipment": self.request.GET.get('shipment', 0),
                   }
        return initial

    def post(self, request, *args, **kwargs):
        if request.user.is_staff:
            self._compute_total_fee(request)
            rst = super(CreateShippingView,self).post(request, *args, **kwargs)
            self._send_shipping_fee(request)
            return rst
        else:
            return HttpResponseRedirect('/')


class EditShippingView(BaseShippingView, UpdateView):
    shipping_id = None

    def get_initial(self):
        if self.shipping_id is None:
            return super(EditShippingView, self).get_initial()
        initial = super(EditShippingView, self).get_initial()
        shp = Shipping.objects.get(pk=self.shipping_id)
        initial['carrier'] = shp.carrier
        initial['service'] = shp.service
        return initial

    def get(self, request, shipping_id):
        self.shipping_id = shipping_id
        self.kwargs.update({'pk': shipping_id})
        if request.user.is_staff:
          return super(EditShippingView,self).get(request)
        else:
            return HttpResponseRedirect('/')

    def post(self, request, shipping_id):
        self.shipping_id = shipping_id
        self.kwargs.update({'pk': shipping_id})
        if request.user.is_staff:
            self._compute_total_fee(request)
            rst = super(EditShippingView,self).post(request)
            self._send_shipping_fee(request)
            return rst
        else:
            return HttpResponseRedirect('/')

class ShippingStatusView(LoginRequiredMixin, View, TemplateResponseMixin):
    template_name = 'shipping_status.html'

    def get_shippings(self):
        self.shippings = Shipping.objects.all()

    def get(self, request, *args, **kwargs):
        self.get_shippings()
        return self.render_to_response(self.__dict__)


class ListOrdersView(LoginRequiredMixin, View, TemplateResponseMixin):
    template_name = 'order_list.html'
    list_current = True

    def _get_order_thumbnail(self, sale_id):
        """
        Using the thumbnail of the first item from the order as the
        order thumbanil image.
        """
        pro_pics = Sale(sale_id).product.pictures.all()
        if len(pro_pics):
            return pro_pics[0].picture
        else:
            return ""

    def set_orders_list(self, request):
        orders = []
        if request.user.is_superuser:
            brand_id = 0
        else:
            brand_id = request.user.get_profile().work_for.pk

        try:
            orders = get_order_list(brand_id)
        except UsersServerError, e:
            self.error_msg = (
                "Sorry, the system meets some issues, our engineers have been "
                "notified, please check back later.")
        for order_dict in orders:
            for order_id, order in order_dict.iteritems():
                order['thumbnail_img'] = \
                    self._get_order_thumbnail(order['first_sale_id'])
        self.orders = orders
        self.page_title = ugettext_lazy("Current Orders")
        return

    def make_page(self):
        """
        make a pagination
        """
        try:
            self.current_page = int(self.request.GET.get('page', '1'))
            p_size = int(
                self.request.GET.get('page_size',
                                     settings.get_page_size(self.request)))
            p_size = (p_size if p_size in settings.CHOICE_PAGE_SIZE
                      else settings.DEFAULT_PAGE_SIZE)
            self.request.session['page_size'] = p_size
        except:
            self.current_page = 1
        paginator = Paginator(self.orders, settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages
        self.range_start = self.current_page - (
            self.current_page % settings.PAGE_NAV_SIZE)
        self.choice_page_size = settings.CHOICE_PAGE_SIZE
        self.current_page_size = settings.get_page_size(self.request)
        self.prev_10 = (self.current_page-settings.PAGE_NAV_SIZE if
                        self.current_page-settings.PAGE_NAV_SIZE > 1 else
                        1)
        self.next_10 = (self.current_page+settings.PAGE_NAV_SIZE if
                        self.current_page+settings.PAGE_NAV_SIZE <= self.page.paginator.num_pages else
                        self.page.paginator.num_pages)
        self.page_nav = self.page.paginator.page_range[self.range_start:self.range_start+settings.PAGE_NAV_SIZE]

    def get(self, request, orders_type=None):
        self.set_orders_list(request)
        self.form = ListOrdersForm()
        self.make_page()
        return self.render_to_response(self.__dict__)

    def post(self, request, orders_type=None):
        self.set_orders_list(request)
        self.form = ListOrdersForm(request.POST)
        if self.form.is_valid():
            order_by1 = self.form.cleaned_data['order_by1']
            order_by2 = self.form.cleaned_data['order_by2']
            self._sort_orders(order_by1, order_by2)
        self.make_page()
        return self.render_to_response(self.__dict__)

    def _sort_orders(self, order_by1, order_by2):
        pass


class OrderDetails(LoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_order_details.html"

    def get(self, request, order_id):
        order_details = {}
        if request.user.is_superuser:
            brand_id = 0
        else:
            brand_id = request.user.get_profile().work_for.pk
        self.order_id = order_id
        try:
            order_details = get_order_detail(order_id, brand_id)
        except UsersServerError, e:
            self.error_msg = (
                "Sorry, the system meets some issues, our engineers have been "
                "notified, please check back later.")
        self.order = order_details
        return self.render_to_response(self.__dict__)