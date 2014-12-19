# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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
from django.http import HttpResponse, HttpResponseBadRequest
from django.template import loader
from django.template.context import Context
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateResponseMixin, View
from pictures.models import ProductPicture
from sorl.thumbnail import get_thumbnail

class UploadProductPictureView(View, TemplateResponseMixin):
    template_name = ""

    def post(self, request):
        if request.FILES:
            new_media = ProductPicture(picture=request.FILES[u'files[]'])
            new_media.save()
            thumb = get_thumbnail(new_media.picture, '40x43')
            t = loader.get_template('_product_preview_thumbnail.html')
            c = Context({ "picture": new_media.picture })
            preview_html = t.render(c)
            to_ret = {'status': 'ok', 'url': new_media.picture.url, 'thumb_url': thumb.url,
                      'pk': new_media.pk, 'preview_html': preview_html}
            return HttpResponse(json.dumps(to_ret), mimetype="application/json")
        raise HttpResponseBadRequest(_("Please upload a picture."))
