import Image
import ImageOps
import StringIO
import os
import magic
import subprocess
from django.conf import settings


def generate_image(image, size):
    size = int(size)
    path = '%s/%s' % (settings.MEDIA_ROOT, image)
    mime = magic.from_file(path, mime=True)
    image = os.path.basename(image)
    if mime.startswith('image/'):
        img = Image.open(path)
    elif mime.startswith('video/'):
        thumbpath = '%s/thumb/%s.jpg' % (settings.MEDIA_ROOT, image)
        if not os.path.exists(thumbpath):
            subprocess.call(['avconv', '-i', path, '-vframes', '1', thumbpath])
        img = Image.open(thumbpath)
    else:
        return None

    if hasattr(img, '_getexif'):
        exif = img._getexif()
    else:
        exif = None
    if exif:
        orientation = exif.get(0x0112, 1)
    else:
        orientation = 1

    rotate = {
        3: Image.ROTATE_180,
        6: Image.ROTATE_270,
        8: Image.ROTATE_90
    }
    if orientation in rotate:
        img = img.transpose(rotate[orientation])

    if size < 256:
        img = ImageOps.fit(img, (size, size), Image.ANTIALIAS)
    elif size < 600:
        img.thumbnail((size, size), Image.ANTIALIAS)
    else:
        width, height = img.size
        if width > size:
            ratio = float(size) / float(width)
            height = int(height * ratio)
            img = img.resize((size, height), Image.ANTIALIAS)

    tdir = '%s/%s/' % (settings.MEDIA_ROOT, size)
    try:
        os.makedirs(tdir)
    except OSError:
        pass
    img.save(tdir + image, 'JPEG')
    data = StringIO.StringIO()
    img.save(data, 'JPEG')
    data.seek(0)
    return data
