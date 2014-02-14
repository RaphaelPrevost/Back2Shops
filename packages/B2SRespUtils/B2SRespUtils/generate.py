import ujson
from jinja2 import Environment, PackageLoader

global temp_env
temp_env = None

def get_env(force=False, package_name=None, package_path=None):
    global temp_env
    if temp_env is not None and not force:
        return temp_env

    if not package_name:
        package_name = "webservice"
    if not package_path:
        package_path = "templates"
    loader=PackageLoader(package_name, package_path)
    temp_env = Environment(loader=loader)
    return temp_env

ENV = get_env()

def _temp_content(template, **data):
    temp = ENV.get_template(template)
    content = temp.render(**data)
    return content

def _pdf_resp(resp, content):
    import weasyprint
    wp = weasyprint.HTML(string=content)
    pdf = wp.render().write_pdf()
    resp.body = pdf
    resp.content_type = "application/pdf"
    return resp

def _html_resp(resp, content):
    resp.body = content
    resp.content_type = "text/html"
    return resp

def _xml_resp(resp, content):
    resp.body = content
    resp.content_type = "application/xml"
    return resp

def _json_resp(resp, data):
    resp.content_type = "application/json"
    resp.body = ujson.dumps(data)
    return resp

def gen_html_resp(template, resp, **data):
    content = _temp_content(template, **data)
    return _html_resp(resp, content)

def gen_pdf_resp(template, resp, **data):
    content = _temp_content(template, **data)
    return _pdf_resp(resp, content)

def gen_xml_resp(template, resp, **data):
    content = _temp_content(template, **data)
    return _xml_resp(resp, content)

def gen_json_resp(resp, data):
    return _json_resp(resp, data)

def gen_text_resp(resp, content):
    return _html_resp(resp, content)