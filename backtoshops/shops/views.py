import json
import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from fouillis.views import BOLoginRequiredMixin
from shops.models import Shop
from shops.forms import ShopForm

class ShopCoordinates(TemplateView):
    def get(self, request, *args, **kwargs):
        shop_id = request.GET.get("shop_id", None)
        toret = {}
        if shop_id:
            shop = Shop.objects.get(pk=shop_id)
            toret['latitude'] = shop.latitude
            toret['longitude'] = shop.longitude
        return HttpResponse(content=json.dumps(toret), mimetype="application/json")

class BaseShopView(BOLoginRequiredMixin):
    template_name = "physical_shop.html"
    form_class = ShopForm
    model = Shop

    def get_success_url(self):
        return reverse("page_shops")

    def get_context_data(self, **kwargs):
        kwargs.update({
            'shop_pk': self.kwargs.get('pk', None),
            'shops': Shop.objects.filter(mother_brand=self.request.user.get_profile().work_for),
            'request': self.request,
            'geonames_username': settings.GEONAMES_USERNAME,
            'media_url': settings.MEDIA_URL,
        })
        return kwargs

class CreateShopView(BaseShopView, CreateView):
    def get_initial(self):
        return {
            "mother_brand": self.request.user.get_profile().work_for
        }
        
    def get_success_url(self):
        new_id = Shop.objects.all().count()
        return reverse('edit_shop',args=[new_id])


class EditShopView(BaseShopView, UpdateView):
    queryset = Shop.objects.all()
    
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("edit_shop",args=[pk])

class DeleteShopView(BaseShopView, DeleteView):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(content=json.dumps({"shop_pk": self.kwargs.get('pk', None)}),
                            mimetype="application/json")

def goto_latest(request):
    latest = Shop.objects.latest()
    HttpResponseRedirect(reverse('edit_shop',args=[latest.id]))
    