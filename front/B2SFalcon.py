import falcon
import re


def compile_uri_template(template):
    """Compile the given URI template string into a pattern matcher.

    Currently only recognizes Level 1 URI templates, and only for the path
    portion of the URI.

    See also: http://tools.ietf.org/html/rfc6570

    Args:
        template: A Level 1 URI template. Method responders must accept, as
        arguments, all fields specified in the template (default '/').

    Returns:
        (template_field_names, template_regex)

    """

    if not isinstance(template, str):
        raise TypeError('uri_template is not a string')

    if not template.startswith('/'):
        raise ValueError("uri_template must start with '/'")

    if '//' in template:
        raise ValueError("uri_template may not contain '//'")

    if template != '/' and template.endswith('/'):
        template = template[:-1]

    expression_pattern = r'{([a-zA-Z][a-zA-Z_]*)}'
    id_expression_patterns = (r'{(id_[a-zA-Z_]*)}', r'{([a-zA-Z_]*id)}')

    # Get a list of field names
    fields = set(re.findall(expression_pattern, template))

    # Convert Level 1 var patterns to equivalent named regex groups
    pattern = re.sub(r'[\.\(\)\[\]\?\*\+\^\|]', r'\\\g<0>', template)
    for ep in id_expression_patterns:
        pattern = re.sub(ep, r'(?P<\1>[^/-]+)', pattern)
    pattern = re.sub(expression_pattern, r'(?P<\1>[^/]+)', pattern)
    pattern = r'\A' + pattern + r'\Z'
    return fields, re.compile(pattern, re.IGNORECASE)


class API(falcon.API):

    def add_route(self, uri_template, resource):
        uri_fields, path_template = compile_uri_template(uri_template)
        method_map, na_responder = falcon.api_helpers.create_http_method_map(
            resource, uri_fields, self._before, self._after)

        self._routes.insert(0, (path_template, method_map, na_responder))

