from webservice.api_key import ApiKeyResource
from webservice.payment import PaymentResource

urlpatterns = {
    '/webservice/1.0/pub/apikey.pem': ApiKeyResource,
    '/webservice/1.0/private/payment/init': PaymentResource,
}
