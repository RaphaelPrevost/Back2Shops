import hashlib
import hmac
import weasyprint

from common.template import ENV

def _temp_content(template, **data):
    temp = ENV.get_template(template)
    content = temp.render(**data)
    return content

def _pdf_resp(resp, content):
    wp = weasyprint.HTML(string=content)
    pdf = wp.render().write_pdf()
    resp.body = pdf
    resp.content_type = "application/pdf"
    return resp

def _html_resp(resp, content):
    resp.body = content
    resp.content_type = "text/html"
    return resp

def gen_html_resp(template, resp, **data):
    content = _temp_content(template, **data)
    return _html_resp(resp, content)

def gen_pdf_resp(template, resp, **data):
    content = _temp_content(template, **data)
    return _pdf_resp(resp, content)

def gen_400_html_resp(resp):
    content = _temp_content('400.html')
    return _html_resp(resp, content)

def gen_400_pdf_resp(resp):
    content = _temp_content('400.html')
    return _pdf_resp(resp, content)

def gen_500_html_resp(resp):
    content = _temp_content('500.html')
    return _html_resp(resp, content)

def gen_500_pdf_resp(resp):
    content = _temp_content('500.html')
    return _pdf_resp(resp, content)

def gen_hmac(key, msg, algorithm=hashlib.sha512):
    return hmac.new(key, msg, algorithm).hexdigest()
