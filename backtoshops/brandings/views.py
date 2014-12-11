import json
import settings

from fouillis.views import AdminLoginRequiredMixin
from brandings.forms import BrandingForm
from brandings.models import Branding
from common.constants import USERS_ROLE

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import UpdateView
from django.core.paginator import EmptyPage
from django.core.paginator import InvalidPage
from django.core.paginator import Paginator


class BaseBrandingView(AdminLoginRequiredMixin):
    template_name = "branding.html"
    form_class = BrandingForm
    model = Branding

    def get_context_data(self, **kwargs):
        # general pagination handling.
        try:
            p_size = int(self.request.GET.get('page_size',settings.get_page_size(self.request)))
            p_size = p_size if p_size in settings.CHOICE_PAGE_SIZE else settings.DEFAULT_PAGE_SIZE
            self.request.session['page_size'] = p_size
        except:
            pass
        self.current_page = int(self.kwargs.get('page','1'))
        paginator = Paginator(self.get_queryset(),settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages
        self.range_start = self.current_page - (self.current_page % settings.PAGE_NAV_SIZE)
        # fill some required fields.
        kwargs.update({
            'choice_page_size': settings.CHOICE_PAGE_SIZE,
            'current_page_size': settings.get_page_size(self.request),
            'page': self.page,
            'prev_10': self.current_page-settings.PAGE_NAV_SIZE if self.current_page-settings.PAGE_NAV_SIZE > 1 else 1,
            'next_10': self.current_page+settings.PAGE_NAV_SIZE if self.current_page+settings.PAGE_NAV_SIZE <= self.page.paginator.num_pages else self.page.paginator.num_pages,
            'page_nav': self.page.paginator.page_range[self.range_start:self.range_start+settings.PAGE_NAV_SIZE],
            'request': self.request,
            'pk': self.kwargs.get('pk', None)
            })
        return kwargs

    def get_initial(self):
        profile = self.request.user.get_profile()
        return {'brand': profile.work_for}

    def get_queryset(self):
        profile = self.request.user.get_profile()
        return Branding.objects.filter(for_brand=profile.work_for)

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

