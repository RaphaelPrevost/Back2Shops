import json
from django.http import HttpResponse
from django.template import loader
from django.template.context import Context
from django.views.generic.base import TemplateResponseMixin, View
from models import BrandAttribute
from fouillis.views import BOLoginRequiredMixin
from sales.models import ProductPicture
from sorl.thumbnail import get_thumbnail

class BrandAttributeView(BOLoginRequiredMixin, View, TemplateResponseMixin):
    template_name = ""

    def get(self, request):
        term = request.GET.get('term', None)
        if not term:
            return HttpResponse(json.dumps(''))
        attrs = BrandAttribute.objects.filter(mother_brand=request.user.get_profile().work_for).filter(name__icontains=term)
        ret_json = []
        t = loader.get_template("_brand_attribute_list_item.html")
        for attr in attrs:
            c = Context({'texture': attr.texture, 'name': attr.name})
            ret_json.append({
                'value': attr.pk,
                'label': t.render(c),
                'premium_type': attr.premium_type,
                'premium_amount': attr.premium_amount,
                'premium_price':attr.premium_price,
                'name': attr.name,
                'texture': get_thumbnail(attr.texture, "15x15").url if attr.texture else None
            })
        return HttpResponse(json.dumps(ret_json), mimetype="application/json")

    def post(self, request):
        to_ret = {}
        pk = request.POST.get('pk', None)
        if pk:
            pk = int(pk)
        name = request.POST.get('name', None)
        premium_type = request.POST.get('premium_type',None)
        premium_amount = request.POST.get('premium_amount',None)
        premium_price = request.POST.get('premium_price',None)
        texture = request.FILES.get('texture_file', None)
        preview_pk = request.POST.get('preview_pk', None)

        success = False
        if pk != -1:
            ba = BrandAttribute.objects.get(pk=pk)
        else:
            ba = BrandAttribute(mother_brand=request.user.get_profile().work_for)
        if name: ba.name = name
        if premium_type: ba.premium_type = premium_type
        if premium_amount: ba.premium_amount = premium_amount
        if premium_price: ba.premium_price = premium_price
        if texture: ba.texture = texture
        ba.save()
        pk = ba.pk
        success = True
        texture_thumb = None
        if ba.texture:
            texture_thumb = get_thumbnail(ba.texture, "15x15").url
        to_ret.update({'pk': pk, 'success': success, 'premium_type':premium_type,'premium_amount':premium_amount, 'premium_price': premium_price, 'texture_thumb': texture_thumb})

        if preview_pk:
            p = ProductPicture.objects.get(pk=preview_pk)
            to_ret.update({'preview_thumb': get_thumbnail(p.picture, "39x43").url, 'preview_pk': p.pk})
            p.brand_attribute = ba
            p.save()

        return HttpResponse(json.dumps(to_ret), mimetype="application/json")
