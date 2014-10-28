import falcon

def monkey_patch():
    # patch falcon response to add more Set-Cookies in the header
    from B2SUtils.falcon_patch import Response
    falcon.api.Response = Response

