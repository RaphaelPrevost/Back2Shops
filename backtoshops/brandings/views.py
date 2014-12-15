import json
import settings

from brandings.forms import BrandingForm
from brandings.models import Branding
from common.admin_view import BaseAdminView

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import UpdateView


class BaseBrandingView(BaseAdminView):
    template_name = "branding.html"
    form_class = BrandingForm
    model = Branding

    def get_initial(self):
        return {'brand': self.brand()}

    def get_queryset(self):
        return Branding.objects.filter(for_brand=self.brand())

class CreateBrandingView(BaseBrandingView, CreateView):
    def get_success_url(self):
        return reverse('edit_branding',args=[self.object.id])

class EditBrandingView(BaseBrandingView, UpdateView):
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("edit_branding",args=[pk])

class DeleteBrandingView(BaseBrandingView, DeleteView):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(
            content=json.dumps({"branding_pk": self.kwargs.get('pk', None)}),
            mimetype="application/json")

