from webservice import crypto
from webservice import download
from webservice import upload

urlpatterns = {
    r'/webservice/1.0/pub/apikey.pem': crypto.APIPubKey,
    r'/webservice/1.0/private/upload': upload.Collection,

    r'/js/{name}': download.JsItem,
    r'/js/{subpath}/{name}': download.JsItem,
    r'/css/{name}': download.CssItem,
    r'/css/{subpath}/{name}': download.CssItem,
    r'/img/{name}': download.ImgItem,
    r'/img/{subpath}/{name}': download.ImgItem,
    r'/html/{name}': download.HtmlItem,
    r'/html/{subpath}/{name}': download.HtmlItem,
}
