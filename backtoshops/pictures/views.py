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
