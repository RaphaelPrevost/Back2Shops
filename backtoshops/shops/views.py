import json
import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from fouillis.views import LoginRequiredMixin
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

class BaseShopView(LoginRequiredMixin):
    template_name = "physical_shop.html"
    form_class = ShopForm
    model = Shop

    def get_success_url(self):
        return reverse("page_shops")

    def get_context_data(self, **kwargs):
        shops = Shop.objects.filter(mother_brand=self.request.user.get_profile().work_for)
        if not self.request.user.is_staff: #operator
            shops = shops.filter(pk__in=self.request.user.get_profile().shops.all())
        kwargs.update({
            'shop_pk': self.kwargs.get('pk', None),
            'shops': shops,
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
    
    def post(self, request, *args, **kwargs):
        if request.user.is_staff:
            return super(CreateShopView,self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect('/')    
        
    def get_success_url(self):
        new_id = Shop.objects.all().count()
        return reverse('edit_shop',args=[new_id])


class EditShopView(BaseShopView, UpdateView):
    queryset = Shop.objects.all()

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk',None)
        if request.user.is_staff or len(request.user.get_profile().shops.filter(pk=pk))>0:
            return super(EditShopView,self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect('/')
    
    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk',None)
        if request.user.is_staff or len(request.user.get_profile().shops.filter(pk=pk))>0:
            return super(EditShopView,self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect('/')
        
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("edit_shop",args=[pk])

class DeleteShopView(BaseShopView, DeleteView):
    def delete(self, request, *args, **kwargs):
        if request.user.is_staff:
            self.object = self.get_object()
            self.object.delete()
            return HttpResponse(content=json.dumps({"shop_pk": self.kwargs.get('pk', None)}),
                                mimetype="application/json")
        else:
            return HttpResponse(content=json.dumps({"shop_pk": "N/A"}), mimetype='application/json')