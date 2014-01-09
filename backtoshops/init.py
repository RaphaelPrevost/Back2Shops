from sorl.thumbnail.base import ThumbnailBackend as _ThumbnailBackend
from sorl.thumbnail import base


patched = {}
class CustomThumbnailBackend(_ThumbnailBackend):
    def get_thumbnail(self, file, geometry_string, **options):
        thumbnail = super(CustomThumbnailBackend, self).get_thumbnail(file, geometry_string, **options)
        if not thumbnail.exists():
            super(CustomThumbnailBackend, self).delete(thumbnail)
            thumbnail = super(CustomThumbnailBackend, self).get_thumbnail(file, geometry_string, **options)
        return thumbnail

def monkey_patch_for_thumbnail():
    global patched
    patched['thumbnail'] = True
    base.ThumbnailBackend = CustomThumbnailBackend

def monkey_patch():
    global patched
    if not patched.get('thumbnail'):
        monkey_patch_for_thumbnail()
