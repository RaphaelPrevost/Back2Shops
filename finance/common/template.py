from jinja2 import Environment, PackageLoader

global temp_env
temp_env = None

def get_env(force=False):
    global temp_env
    if temp_env is not None and not force:
        return temp_env

    temp_env = Environment(loader=PackageLoader('webservice'))
    return temp_env

ENV = get_env()


