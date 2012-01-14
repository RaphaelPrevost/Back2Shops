from models import GlobalSettings

def get_setting(key):
    try:
        val = GlobalSettings.objects.get(key=key).value
    except:
        val = None
    return val

