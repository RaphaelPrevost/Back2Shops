import logging
import settings
import types
import ujson

from decimal import Decimal
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.base import View, TemplateResponseMixin
from fouillis.views import LoginRequiredMixin

from common import carriers
from common.orders import send_shipping_fee
from orders.models import Shipping
from orders.forms import ShippingForm
from shippings.models import Carrier, Service

def _api_fee(carr_cls, data):
    handling_fee = Decimal(data.get('handling_fee') or 0)
    addr_orig = data.get('addr_orig')
    addr_dest = data.get('addr_dest')
    service = data.get('service')
    weight = float(data.get('weight') or 0)

    rate = carr_cls.getRate(addr_orig, addr_dest, service, weight)
    return Decimal(rate) + handling_fee

def _no_api_fee(data):
    return Decimal(data.get('ship_and_handling_fee') or 0)

def compute_fee(data):
    carrer_id = data.get('carrier')
    carr = Carrier.objects.get(pk=carrer_id)
    carr_flag = carr and carr.flag
    cls_name = carr_flag.upper() + carriers.CARRIER_CLS_SURFFIX
    cls = getattr(carriers, cls_name)
    if cls and type(cls) is types.ClassType:
        total_fee = _api_fee(cls, data)
    else:
        total_fee = _no_api_fee(data)
    return total_fee

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
        id_order = request.POST.get('order')
        id_postage = request.POST.get('service')
        shipping_fee = request.POST.get('total_fee')
        try:
            assert is_decimal(id_order), 'order: %s should be a digit' % id_order
            assert is_decimal(id_postage), 'service: %s should be a digit' % id_postage
            assert is_decimal(shipping_fee), 'shipping fee: %s should be a digit' % shipping_fee
        except AssertionError, e:
            logging.error('send_shipping_fee args error: %s' % e,
                          exc_info=True)
            raise
        send_shipping_fee(id_order, id_postage, shipping_fee)

    def _compute_total_fee(self, request):
        total_fee = compute_fee(request.POST)
        request.POST.update({'total_fee': total_fee})
        return total_fee


class CreateShippingView(BaseShippingView, CreateView):
    def get_initial(self):
        initial = {"addr_orig": self.request.GET.get('addr_orig', 'orignal'),
                   "addr_dest": self.request.GET.get('addr_dest', 'dest'),
                   "order": self.request.GET.get('order', 0),
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
