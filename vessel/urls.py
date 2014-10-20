from webservice import api_key
from webservice import search
from webservice import user_fleet
from webservice import vessel

urlpatterns = {
    r'/webservice/1.0/pub/apikey.pem': api_key.ApiKeyResource,

    r'/webservice/1.0/protected/vessel/search': search.SearchVesselResource,
    r'/webservice/1.0/protected/port/search': search.SearchPortResource,
    r'/webservice/1.0/protected/vessel/details': vessel.VesselDetailResource,
    r'/webservice/1.0/protected/vessel/path': vessel.VesselNaviPathResource,

    r'/webservice/1.0/private/user_fleet': user_fleet.UserFleetResource,
}
