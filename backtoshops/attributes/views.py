# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


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
from sales.forms import BrandAttributeForm


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
                'texture': attr.texture.url if attr.texture else None,
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
        premium_type = request.POST.get('premium_type', None)
        try:
            premium_amount = request.POST.get('premium_amount', None)
        except:
            premium_amount = None
        texture = request.FILES.get('texture_file', None)
        ba_index = request.POST.get('ba_index', None)
        previews = request.POST.get('previews', '[]')
        if previews:
            previews = json.loads(previews)

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
        to_ret.update({
            'success': success,
            'err': err,
            'pk': pk,
            'name': name,
            'premium_type': premium_type,
            'premium_amount': premium_amount,
            'texture': ba.texture.url if ba.texture else None,
        })
        prefix = "brand_attributes-%s" % ba_index
        data = {
            '%s-ba_id' % prefix: pk,
            '%s-name' % prefix: name,
            '%s-premium_type' % prefix: premium_type,
            '%s-premium_amount' % prefix: premium_amount,
            '%s-texture' % prefix: ba.texture.url if ba.texture else None,
        }

        preview_prefix = "%s-previews" % prefix
        for index, p_data in enumerate(previews):
            p = ProductPicture.objects.get(pk=p_data['pk'])
            p.brand_attribute = ba
            p.sort_order = p_data['sort_order']
            p.save()
            _prefix = "%s-%s" % (preview_prefix, index)
            data.update({
                "%s-pk" % _prefix: p.pk,
                "%s-url" % _prefix: get_thumbnail(p.picture, "187x187").url,
                "%s-sort_order" % _prefix: p.sort_order,
            })
        data.update({
            '%s-TOTAL_FORMS' % preview_prefix: len(previews),
            '%s-INITIAL_FORMS' % preview_prefix: 0,
            '%s-MAX_NUM_FORMS' % preview_prefix: 1000,
        })
        t = loader.get_template("add_sale_product_edit_attr.html")
        c = Context({'ba': BrandAttributeForm(data=data, prefix=prefix)})
        to_ret['ba_html'] = t.render(c)
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
