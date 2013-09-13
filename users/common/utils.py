import hashlib
import re
import ujson
from falcon import request_helpers
from constants import HASH_ALGORITHM_NAME

email_pattern = re.compile(
    r"^([0-9a-zA-Z]+[-._+&amp;])*[0-9a-zA-Z]+@([-0-9a-zA-Z]+.)+[a-zA-Z]{2,6}$")

def is_valid_email(email):
    return email and email_pattern.match(email)

def hashfn(algorithm, text):
    # Retrieves the appropriate hash function
    if algorithm not in HASH_ALGORITHM_NAME:
        raise ValueError("Unknown algorithm.")
    if text == "":
        raise ValueError("Missing text.")
    h = hashlib.new(HASH_ALGORITHM_NAME[algorithm])
    # XXX repeated calls to update() simply concatenate text!
    h.update(text)
    return h.hexdigest()

def get_preimage(algorithm, iterations, salt, password):
    # Computes the pre-image of the authenticator token.
    # This pre-image is used in the user session cookie.
    if iterations <= 0:
        raise ValueError("Bad iterations count.")
    if salt == "" or password == "":
        raise ValueError("Empty salt or password.")
    while iterations > 0:
        salt = result = hashfn(algorithm, salt + password)
        iterations -= 1
    return result

def get_authenticator(algorithm, preimage):
    # Computes the authenticator from a pre-image.
    # This can be used to check the user's cookie.
    return hashfn(algorithm, preimage)

def get_hexdigest(algorithm, iterations, salt, password):
    # This function computes the authenticator.
    # This authenticator is stored in database.
    preimage = get_preimage(algorithm, iterations, salt, password)
    return get_authenticator(algorithm, preimage)

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

