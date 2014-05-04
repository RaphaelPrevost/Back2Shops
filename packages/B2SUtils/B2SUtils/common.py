import cgi

def parse_form_params(req, resp, params):
    if req.method == 'GET':
        return
    if 'x-www-form-urlencoded' not in req.content_type:
        return

    # in falcon 0.1.6 req._params doesn't support form params
    try:
        body = req.stream.read(req.content_length)
        if req.query_string.strip() == "":
            req.query_string = body
        else:
            req.query_string += "&"
            req.query_string += body
    except:
        pass
    else:
        form_params = cgi.parse_qs(body)
        for p in form_params:
            form_params[p] = form_params[p][0]
        import logging
        req._params.update(form_params)

