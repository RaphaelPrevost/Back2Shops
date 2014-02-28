import json
import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from fouillis.views import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from promotion.forms import GroupForm
from promotion.models import Group, TypesInGroup, SalesInGroup
from sales.models import Sale, ProductType
from shops.models import Shop


class BasePromotionView(LoginRequiredMixin):
    template_name = "promotion_group.html"
    form_class = GroupForm
    model = Group

    def get_success_url(self):
        return reverse("page_promotion")

    def _profile_shops(self):
        if not self.request.user.is_staff:
            return self.request.user.get_profile().shops.all()

    def _get_groups_by_user(self):
        brand = self.request.user.get_profile().work_for
        kwargs = {'brand': brand}

        profile_shops = self._profile_shops()
        if profile_shops is not None:
            kwargs['shop__in'] = profile_shops

        return Group.objects.filter(**kwargs)

    def _get_shops_by_user(self):
        brand = self.request.user.get_profile().work_for
        shops_kwargs = {'mother_brand': brand}

        profile_shops = self._profile_shops()
        if profile_shops is not None:
            shops_kwargs['pk__in'] = profile_shops

        return Shop.objects.filter(**shops_kwargs)

    def _get_sales(self, brand, shops):
        sales = Sale.objects.filter(mother_brand=brand)
        # filter sales by shops for shop keeper user.
        exclude_ids = []
        if not self.request.user.is_staff:
            for sale in sales.all():
                exclude = True
                for shop in sale.shops.all():
                    if shop in shops:
                        exclude = False
                        break
                if exclude:
                    exclude_ids.append(sale.pk)
        sales.exclude(pk__in=exclude_ids)
        return sales

    def get_initial(self):
        brand = self.request.user.get_profile().work_for
        types = ProductType.objects.all()
        shops = self._get_shops_by_user()
        sales = self._get_sales(brand, shops)
        return {
            "brand": brand,
            "shops": shops,
            "types": types,
            "sales": sales.all(),
            "is_staff": self.request.user.is_staff,
        }

    def get_context_data(self, **kwargs):
        groups = self._get_groups_by_user()
        try:
            p_size = int(self.request.GET.get('page_size',settings.get_page_size(self.request)))
            p_size = p_size if p_size in settings.CHOICE_PAGE_SIZE else settings.DEFAULT_PAGE_SIZE
            self.request.session['page_size'] = p_size
        except:
            pass
        self.current_page = int(self.kwargs.get('page','1'))
        paginator = Paginator(groups,settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages
        self.range_start = self.current_page - (self.current_page % settings.PAGE_NAV_SIZE)    
        kwargs.update({
            'promotion_pk': self.kwargs.get('pk', None),
            'groups': self.page,
            'request': self.request,
            'media_url': settings.MEDIA_URL,
            'choice_page_size': settings.CHOICE_PAGE_SIZE,
            'current_page_size': settings.get_page_size(self.request),
            'page': self.page,
            'prev_10': self.current_page-settings.PAGE_NAV_SIZE if self.current_page-settings.PAGE_NAV_SIZE > 1 else 1,
            'next_10': self.current_page+settings.PAGE_NAV_SIZE if self.current_page+settings.PAGE_NAV_SIZE <= self.page.paginator.num_pages else self.page.paginator.num_pages,
            'page_nav': self.page.paginator.page_range[self.range_start:self.range_start+settings.PAGE_NAV_SIZE],       
        })
        return kwargs

    def _get_promotion_types(self, brand):
        pass


class CreatePromotionView(BasePromotionView, CreateView):
    def get_success_url(self):
        return reverse('page_promotion')


class EditPromotionView(BasePromotionView, UpdateView):
    def get_initial(self):
        initial = super(EditPromotionView, self).get_initial()
        pk = self.kwargs.get('pk')
        group_kwargs = {'group_id': pk}

        profile_shops = self._profile_shops()
        if profile_shops is not None:
            group_kwargs['group__shop__in'] = profile_shops

        type_choices = [
            tig.type for tig in TypesInGroup.objects.filter(**group_kwargs)]

        sales_choices = [
            sig.sale for sig in SalesInGroup.objects.filter(**group_kwargs)]


        group = Group.objects.get(pk=pk)
        initial.update({
            "type_choices": type_choices,
            "sales_choices": sales_choices,
            "pk": pk,
            'name': group.name,
            'shop': group.shop
            })
        return initial

    def get(self, request, *args, **kwargs):
        queryset = self._get_groups_by_user()
        self.queryset = queryset
        pk = self.kwargs.get('pk',None)
        if len(queryset.filter(pk=pk))>0:
            return super(EditPromotionView,self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect('/')
    
    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk',None)
        queryset = Group.objects.filter(brand=request.user.get_profile().work_for)
        if len(queryset.filter(pk=pk))>0:
            return super(EditPromotionView,self).post(request, *args, **kwargs)
        else:
            return HttpResponseRedirect('/')
        
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("edit_promotion",args=[pk])


class DeletePromotionView(BasePromotionView, DeleteView):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(
            content=json.dumps(
                {"group_pk": self.kwargs.get('pk', None)}),
            mimetype="application/json")
