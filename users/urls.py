from webservice.accounts import UserResource
from webservice.auth import UserLoginResource

urlpatterns = {
    '/webservice/1.0/pub/account': UserResource,
    '/webservice/1.0/pub/connect': UserLoginResource,
}
