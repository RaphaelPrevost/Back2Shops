import settings
import json
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponse
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from fouillis.views import AdminLoginRequiredMixin
from routes.models import HtmlMeta, Route, RouteParam
from routes.forms import RouteForm, HTMLMetasForm, RouteParamForm


class BaseRouteView(AdminLoginRequiredMixin):
    template_name = "route.html"
    model = Route
    form_class = RouteForm
    meta_form = inlineformset_factory(Route, HtmlMeta, form=HTMLMetasForm, extra=0)
    routeparam_form = inlineformset_factory(Route, RouteParam, form=RouteParamForm, extra=0)

    def get_success_url(self):
        return reverse("routes")

    def get_context_data(self, **kwargs):
        routes = self.get_routes()

        try:
            p_size = int(self.request.GET.get('page_size', settings.get_page_size(self.request)))
            p_size = p_size if p_size in settings.CHOICE_PAGE_SIZE else settings.DEFAULT_PAGE_SIZE
            self.request.session['page_size'] = p_size
        except:
            pass

        self.current_page = int(self.kwargs.get('page', '1'))
        paginator = Paginator(routes, settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages

        self.range_start = self.current_page - (self.current_page % settings.PAGE_NAV_SIZE)
        kwargs.update({
            'pk': self.kwargs.get('pk', None),
            'routes': self.page,
            'meta_form': self.meta_form,
            'routeparam_form': self.routeparam_form,
            'request': self.request
        })
        return kwargs

    def get_form_kwargs(self):
        kwargs = super(BaseRouteView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_routes(self):
        return Route.objects.all()


class CreateRouteView(BaseRouteView, CreateView):
    form_class = RouteForm

    def get_initial(self):
        if self.request.user.is_superuser:
            return {}

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            route = form.save(commit=False)
            meta_form = self.meta_form(data=self.request.POST, instance=route)
            routeparam_form = self.routeparam_form(data=self.request.POST, instance=route)

            if meta_form.is_valid() and routeparam_form.is_valid():
                form.save(commit=True)
                meta_form.save()
                routeparam_form.save()
                return self.form_valid(form)

        return self.form_invalid(form)

    def get_success_url(self):
        return reverse('edit_route', args=[self.object.id])


class EditRouteView(BaseRouteView, UpdateView):
    form_class = RouteForm

    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse('edit_route', args=[pk])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.meta_form = self.meta_form(instance=self.get_object())
        self.routeparam_form = self.routeparam_form(instance=self.get_object())

        return super(BaseRouteView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            route = form.save(commit=False)
            meta_form = self.meta_form(data=self.request.POST, instance=route)
            routeparam_form = self.routeparam_form(data=self.request.POST, instance=route)

            if meta_form.is_valid() and routeparam_form.is_valid():
                form.save(commit=True)
                meta_form.save()
                routeparam_form.save()
                return self.form_valid(form)

        return self.form_invalid(form)


class DeleteRouteView(BaseRouteView, DeleteView):

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(content=json.dumps({'pk': self.kwargs.get('pk', None)}),
                            mimetype="application/json")


def get_route_params(request, *args, **kwargs):
    route_id = kwargs.get('pid', None)

    routeParam = RouteParam.objects.filter(route=route_id)
    datas = [(x.pk, x.name, x.is_required) for x in routeParam]
    return HttpResponse(json.dumps(datas), mimetype='application/json')


def get_page_roles(request, *args, **kwargs):
    term = request.GET.get('term', None)

    if not term:
        return HttpResponse(json.dumps(''))

    datas = [({'value': x.get('page_role')}) for x in Route.objects.values('page_role').filter(page_role__icontains=term).distinct()]
    return HttpResponse(json.dumps(datas), mimetype='application/json')

