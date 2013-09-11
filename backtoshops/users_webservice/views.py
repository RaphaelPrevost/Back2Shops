import json
from django.db.utils import DatabaseError
from django.http import HttpResponse

from accounts.models import EndUser
from users_webservice.forms import UserCreationForm

def gen_json_response(data_dict):
    return HttpResponse(content=json.dumps(data_dict),
                        mimetype="application/json")

def create_user(request):
    if request.method == 'GET':
        return gen_json_response({"res": "FAILURE",
                                  "err": "INVALID_REQUEST"})
    try:
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            user = EndUser()
            user.email = form.cleaned_data["email"]
            user.set_password(form.cleaned_data["password"])
            user.save()
            return gen_json_response({"res": "SUCCESS",
                                      "err": ""})
        else:
            return gen_json_response({"res": "FAILURE",
                                      "err": form.get_response_error()})
    except DatabaseError, e:
        return gen_json_response({"res": "FAILURE",
                                  "err": "ERR_DB",
                                  "ERR_SQLDB": str(e)})
