from django import template
from django.template.base import Variable

register = template.Library()

@register.tag(name='counter')
def do_counter(parser, token):
    try:
        tag_name, args = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("'counter' node requires a variable name.")
    return CounterNode(args)

class CounterNode(template.Node):
    def __init__(self, varname):
        self.varname = varname

    def render(self, context):
        try:
            var = Variable(self.varname).resolve(context)
        except:
            var = 0
        #deep = len(context.dicts)-1
        context.dicts[0][self.varname] = var+1
        return ''