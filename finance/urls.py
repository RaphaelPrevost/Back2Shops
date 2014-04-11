from webservice.api_key import ApiKeyResource
from webservice.payment import PaymentFormResource
from webservice.payment import PaymentInitResource

urlpatterns = {
    '/webservice/1.0/pub/apikey.pem': ApiKeyResource,
    '/webservice/1.0/private/payment/form': PaymentFormResource,
    '/webservice/1.0/private/payment/init': PaymentInitResource,
}
