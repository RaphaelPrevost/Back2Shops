from webservice.api_key import ApiKeyResource

urlpatterns = {
    '/webservice/1.0/pub/apikey.pem': ApiKeyResource,
}
