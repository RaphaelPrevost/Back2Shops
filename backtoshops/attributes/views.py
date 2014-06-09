import json
from django.http import HttpResponse
from django.template import loader
from django.template.context import Context
from django.views.generic.base import TemplateResponseMixin, View
from sorl.thumbnail import get_thumbnail

from attributes.models import BrandAttribute
from attributes.models import CommonAttribute
from fouillis.views import OperatorUpperLoginRequiredMixin
from fouillis.views import manager_upper_required
from sales.models import ProductPicture


class BrandAttributeView(OperatorUpperLoginRequiredMixin,
                         View,
                         TemplateResponseMixin):
    template_name = ""

    def get(self, request):
        term = request.GET.get('term', None)
        if not term:
            return HttpResponse(json.dumps(''))
        attrs = BrandAttribute.objects.filter(
            mother_brand=request.user.get_profile().work_for
        ).filter(name__icontains=term)
        ret_json = []
        t = loader.get_template("_brand_attribute_list_item.html")
        for attr in attrs:
            c = Context({'texture': attr.texture, 'name': attr.name})
            ret_json.append({
                'value': attr.pk,
                'label': t.render(c),
                'premium_type': attr.premium_type,
                'premium_amount': attr.premium_amount,
                'name': attr.name,
                'texture': get_thumbnail(attr.texture, "15x15").url if attr.texture else None
            })
        return HttpResponse(json.dumps(ret_json), mimetype="application/json")

    def post(self, request):
        return manager_upper_required(self._post,
                                      login_url="bo_login")(request)

    def _post(self, request):
        to_ret = {}
        pk = request.POST.get('pk', None)
        if pk:
            pk = int(pk)
        name = request.POST.get('name', None)
        premium_type = request.POST.get('premium_type',None)
        try:
            premium_amount = request.POST.get('premium_amount',None)
        except:
            premium_amount = None
        texture = request.FILES.get('texture_file', None)
        preview_pk = request.POST.get('preview_pk', None)

        success = False
        if pk != -1:
            try: # a fail-safe for not-found
                ba = BrandAttribute.objects.get(pk=pk)
            except:
                ba = BrandAttribute(mother_brand=request.user.get_profile().work_for)
        else:
            ba = BrandAttribute(mother_brand=request.user.get_profile().work_for)
        if name: ba.name = name
        if premium_type: ba.premium_type = premium_type
        if premium_amount: ba.premium_amount = premium_amount
        if texture: ba.texture = texture
        try:
            ba.save()
            pk = ba.pk
            success = True
            err = ''
        except Exception, e:
            success = False
            err = str(e)
        texture_thumb = None
        if ba.texture:
            texture_thumb = get_thumbnail(ba.texture, "15x15").url
        to_ret.update({'pk': pk,
                       'success': success,
                       'err': err,
                       'premium_type': premium_type,
                       'premium_amount': premium_amount,
                       'texture_thumb': texture_thumb})

        if preview_pk:
            p = ProductPicture.objects.get(pk=preview_pk)
            to_ret.update({
                'preview_thumb': get_thumbnail(p.picture, "39x43").url,
                'preview_pk': p.pk})
            p.brand_attribute = ba
            p.save()

        return HttpResponse(json.dumps(to_ret), mimetype="application/json")


def get_item_attributes(request, *args, **kwargs):
    item_attrs_list = []
    item_attrs = CommonAttribute.objects.filter(
        for_type_id=kwargs.get('tid', None))
    for attr in item_attrs:
        item_attrs_list.append({'label': attr.name,
                                'value': attr.id,
                                'valid': attr.valid})
    return HttpResponse(json.dumps(item_attrs_list),
                        mimetype='application/json')
