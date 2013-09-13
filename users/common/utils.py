import hashlib
import re
import ujson
from falcon import request_helpers
from constants import HASH_ALGORITHM_NAME

email_pattern = re.compile(
    r"^([0-9a-zA-Z]+[-._+&amp;])*[0-9a-zA-Z]+@([-0-9a-zA-Z]+.)+[a-zA-Z]{2,6}$")

def is_valid_email(email):
    return email and email_pattern.match(email)

def get_hexdigest(algorithm, iteration_count, salt, raw_password):
    if algorithm not in HASH_ALGORITHM_NAME:
        raise ValueError("Got unknown password algorithm type in password.")

    h = hashlib.new(HASH_ALGORITHM_NAME[algorithm])
    h.update(salt + raw_password)
    result = h.hexdigest()

    iteration_count = iteration_count - 1
    if iteration_count > 0:
        return get_hexdigest(algorithm, iteration_count, result, raw_password)
    else:
        return result

def parse_form_params(req, resp, params):
    if req.method == 'GET':
        return
    if req.content_type != 'application/x-www-form-urlencoded':
        return

    # in falcon 0.1.6 req._params doesn't support form params
    try:
        body = req.stream.read(req.content_length)
    except:
        pass
    else:
        req._params.update(request_helpers.parse_query_string(body))

def gen_json_response(resp, data_dict):
    resp.content_type = "application/json"
    resp.body = ujson.dumps(data_dict)
    return resp

