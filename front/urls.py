from views.homepage import HomepageResource
from views.login import LoginResource
from views.payment import PaypalSuccessResource
from views.payment import PaypalFailureResource
from views.payment import PaymentFormResource
from views.product import ProductInfoResource
from views.product import ProductListResource
from views.register import RegisterResource
from views.user import UserResource
from webservice.aux import AuxResource

urlpatterns = {
    r'/': HomepageResource,
    r'/login': LoginResource,
    r'/register': RegisterResource,
    r'/user_info': UserResource,
    r'/products': ProductListResource,
    r'/product_info': ProductInfoResource,
    r'/paypal/{id_trans}/success': PaypalSuccessResource,
    r'/paypal/{id_trans}/failure': PaypalFailureResource,
    r'/webservice/1.0/pub/JSONAPI': AuxResource,

    # TODO: Remove, here just for payment test
    r'/payment/{id_trans}/form': PaymentFormResource,
}
