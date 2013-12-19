from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.base import View

from fouillis.views import LoginRequiredMixin
from shippings.forms import CustomShippingRateFormModel
from shippings.models import CustomShippingRate


class CustomShippingRateView(LoginRequiredMixin, View, TemplateResponseMixin):
    template_name = "_ajax_custom_shipping_rates.html"

    def post(self, request):
        try:
            form = CustomShippingRateFormModel(request.POST, request.FILES)
            if form.is_valid():
                self.new_custom_shipping_rate = form.save(commit=False)
                self.new_custom_shipping_rate.seller = \
                    request.user.get_profile().work_for
                self.new_custom_shipping_rate.save()
                messages.success(
                    request,
                    _("The custom shipping rate has been successfully created."
                    ))
                self.custom_shipping_rates = \
                    CustomShippingRate.objects.filter(
                        seller=request.user.get_profile().work_for)
            else:
                self.errors = form.errors
        except Exception as e:
            self.errors = e
        return self.render_to_response(self.__dict__)
