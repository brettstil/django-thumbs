# -*- encoding: utf-8 -*-
"""
django-thumbs by Antonio Melé
http://django.es
"""

from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile
from django.core.files.base import ContentFile
from django.conf import settings

try:
    from PIL import Image, ImageOps, ExifTags, ImageFile
except ImportError:
    import Image
    import ImageOps
    import ExifTags
    import ImageFile

import cStringIO
import logging
logger = logging.getLogger(__name__)
import re

THUMBS_DELIMITER = getattr(settings, 'THUMBS_DELIMITER', '-')
# always save jpg thumbs regardless of original file format
THUMBS_JPG = getattr(settings, 'THUMBS_JPG', True)
THUMBS_QUALITY = getattr(settings, 'THUMBS_QUALITY', 75)  # JPEG
THUMBS_OPTIMIZE = getattr(settings, 'THUMBS_OPTIMIZE', True)  # JPEG PNG
THUMBS_PROGRESSIVE = getattr(settings, 'THUMBS_PROGRESSIVE', False)  # JPEG
# autorotate thumbs based on exif orientation
THUMBS_AUTOROTATE = getattr(settings, 'THUMBS_AUTOROTATE', True)

VALID_RESIZES = ['crop', 'scale']
VALID_ORIGINAL_EXT = ['jgp', 'jpeg', 'png', 'gif']
RE_CODE = '^[0-9a-z]+$'
RE_WXH = '^(\d+x\d+|\d+x|x\d+)$'


class SizeError(Exception):
    pass


class OriginalError(Exception):
    pass


def sting2tuple(wxh, original_w_h):
    '''
    Converts a wxh string into a tuple of integers ready for PIL.

    Handles fixed width '200x' or fixed height 'x100' size by setting
    the empty string height or width, respectively.

    Cropping is not relevant to fixed width since the image is always
    scaled down or up to the fixed width.  At this point extremely
    vertical original images, for example 10x500, are still scaled.

    '''

    split = wxh.split('x')
    w = split[0]
    h = split[1]

    if '' in split:
        original_w, original_h = original_w_h
        # fixed width, '240x'
        if h == '':
            h = int(w) * original_h / original_w
        # fixed height, 'x100'
        elif w == '':
            w = int(h) * original_w / original_h

    return (int(w), int(h))


def resize_content(original, size, format_ext):

    original.seek(0)  # http://code.djangoproject.com/ticket/8222
    image = Image.open(original)

    # convert to RGB if necessary
    if image.mode not in ('L', 'RGB', 'RGBA'):
        image = image.convert('RGB')

    # rotate flip before crop scale
    if THUMBS_AUTOROTATE:
        # http://stackoverflow.com/q/4228530
        found = [k for k, v in ExifTags.TAGS.items() if v == 'Orientation']
        if found:
            tag = found[0]
            if hasattr(image, '_getexif'):  # _getexif only in JPG
                exif = image._getexif()  # returns None if no EXIF
                if exif is not None and tag in exif:
                    orientation = exif[tag]

                    # http://impulseadventure.com/photo/exif-orientation.html
                    # https://github.com/recurser/exif-orientation-examples

                    if orientation in [2, 4, 5, 7]:
                        image = image.transpose(Image.FLIP_LEFT_RIGHT)

                    if orientation == 3 or orientation == 4:
                        image = image.transpose(Image.ROTATE_180)
                    elif orientation == 6 or orientation == 7:
                        image = image.transpose(Image.ROTATE_270)
                    elif orientation == 8 or orientation == 5:
                        image = image.transpose(Image.ROTATE_90)

    w_h = sting2tuple(size['wxh'], image.size)

    # 'crop'
    if 'resize' in size and size['resize'] == 'crop':
        resized = ImageOps.fit(image, w_h, Image.ANTIALIAS)
    # 'scale' default
    else:
        image.thumbnail(w_h, Image.ANTIALIAS)
        resized = image

    # PNG and GIF are the same, JPG is JPEG
    format = format_ext.upper()
    if format == 'JPG':
        format = 'JPEG'

    io = cStringIO.StringIO()

    # http://www.pythonware.com/library/pil/handbook/format-gif.htm
    # http://www.pythonware.com/library/pil/handbook/format-png.htm
    # http://www.pythonware.com/library/pil/handbook/format-jpeg.htm
    if format == 'GIF':
        resized.save(io, format)
    elif format == 'PNG':
        resized.save(io, format, optimize=THUMBS_OPTIMIZE)
    else:  # 'JPEG'
        try:
            resized.save(io, 'JPEG', quality=THUMBS_QUALITY,
                optimize=THUMBS_OPTIMIZE, progressive=THUMBS_PROGRESSIVE)
        except IOError:
            ImageFile.MAXBLOCK = resized.size[0] * resized.size[1]
            resized.save(io, 'JPEG', quality=THUMBS_QUALITY,
                optimize=THUMBS_OPTIMIZE, progressive=THUMBS_PROGRESSIVE)

    return ContentFile(io.getvalue())


def split_original(name):
    '''Splits an original filename into dict with keys base, ext.'''

    if not (isinstance(name, str) or isinstance(name, unicode)):
        raise OriginalError('Invalid name.')
    if not name:
        raise OriginalError('Invalid name.')

    split = name.rsplit('.', 1)
    return {'base': split[0],
        # original name might not have ext
        'ext': split[1] if len(split) == 2 else ''}


def determine_thumb(size, name, jpg=THUMBS_JPG, delimiter=THUMBS_DELIMITER):
    '''Determine a thumbnail filename, based only on the original filename.'''

    base_ext = split_original(name)

    base = '%s%s%s' % (base_ext['base'], delimiter, size['code'])

    # if always jpg settings
    # convert jpeg to jpg
    if jpg is True:
        return '%s.%s' % (base, 'jpg')

    # no original ext, jpg it
    if base_ext['ext'] == '':
        return '%s.%s' % (base, 'jpg')

    # lowercase ext, validate ext
    ext = base_ext['ext'].lower()
    if ext in VALID_ORIGINAL_EXT:
        # valid, keep original ext
        return '%s.%s' % (base, ext)
    else:
        # not valid, jpg it
        return '%s.%s' % (base, 'jpg')


def validate_size(size):
    '''Validate size dict.'''

    if not isinstance(size, dict):
        raise SizeError('Invalid size.')

    # required
    if not 'code' in size or not re.match(RE_CODE, size['code']):
        raise SizeError('Valid code required, eg, small.')
    if not 'wxh' in size or not re.match(RE_WXH, size['wxh']):
        raise SizeError('Valid wxh required, eg, 400x300.')
    # optional
    if 'resize' in size:
        # optional, but must be valid
        if size['resize'] not in VALID_RESIZES:
            raise SizeError('Invalid resize.')


class ImageThumbsFieldFile(ImageFieldFile):

    def __init__(self, *args, **kwargs):
        super(ImageThumbsFieldFile, self).__init__(*args, **kwargs)

        if self.field.sizes:

            def get_size(self, size):
                if not self:
                    return ''
                else:
                    return determine_thumb(size, self.url)

            for size in self.field.sizes:
                thumb_url = get_size(self, size)
                setattr(self, 'url_%s' % size['code'], thumb_url)

    def save(self, name, content, save=True):

        # original ext in name could be incorrect, .jpg on png, or .xyz
        # but thumb ext is valid from determine_thumb

        # TODO: verify original ext?
        # original.seek(0)  # http://code.djangoproject.com/ticket/8222
        # image = Image.open(original)
        # logger.debug(image.format)

        super(ImageThumbsFieldFile, self).save(name, content, save)

        if self.field.sizes:
            for size in self.field.sizes:
                size_name = determine_thumb(size, self.name)
                # thumb ext is valid out of determine_thumb,
                # split off ext and pass ext in as format
                thumb_base_ext = split_original(size_name)
                size_content = resize_content(content, size,
                    thumb_base_ext['ext'])
                saved_name = self.storage.save(size_name, size_content)
                if saved_name != size_name:
                    raise ValueError(
                        'There is already a file named %s' % size_name)

    def delete(self, save=True):
        # keep self.name before deleting in super delete()
        name = self.name

        super(ImageThumbsFieldFile, self).delete(save)

        if self.field.sizes:
            for size in self.field.sizes:
                size_name = determine_thumb(size, name)
                try:
                    self.storage.delete(size_name)
                except:
                    logger.warn('Delete fail %s' % size_name)


class ImageThumbsField(ImageField):
    attr_class = ImageThumbsFieldFile

    def __init__(self, verbose_name=None, name=None,
            width_field=None, height_field=None, sizes=None, **kwargs):

        # django
        self.verbose_name = verbose_name
        self.name = name
        self.width_field = width_field
        self.height_field = height_field

        # validate each size
        for size in sizes:
            validate_size(size)

        # django-thumbs
        self.sizes = sizes

        super(ImageField, self).__init__(**kwargs)

    def south_field_triple(self):
        from south.modelsinspector import introspector
        field_class = 'django.db.models.fields.files.ImageField'
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)
