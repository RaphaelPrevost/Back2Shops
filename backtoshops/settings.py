from platform import node

DEVELOPMENT_HOST='Nicholass-MacBook-Pro.local'
DEVELOPMENT_HOST = 'ada-pc'

if node() == DEVELOPMENT_HOST:
    from settings_local import *
elif node() == 'debian': #tentatively using this as VPS debian dev setting
    from settings_debian import *
elif node() == 'Ghostwheel': #now i can run the code from my laptop!
    from settings_ghostwheel import *
elif node(): # == PRODUCTION_HOST:
    from settings_production import *
else:
    raise Exception("Cannot determine execution mode for host '%s'.  Please check DEVELOPMENT_HOST and PRODUCTION_HOST in settings_local.py." % node())

