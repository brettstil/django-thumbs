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
    from PIL import Image, ImageOps
except ImportError:
    import Image
    import ImageOps

import cStringIO
import logging
logger = logging.getLogger(__name__)
import re

THUMBS_DELIMITER = getattr(settings, 'THUMBS_DELIMITER', '-')
THUMBS_JPG = getattr(settings, 'THUMBS_JPG', False)
THUMBS_QUALITY = getattr(settings, 'THUMBS_QUALITY', 90)
VALID_RESIZES = ['crop', 'scale']
VALID_ORIGINAL_EXT = ['jgp', 'jpeg', 'png', 'gif']


class SizeError(Exception):
    pass


class OriginalError(Exception):
    pass


def resize_content(original, size, format_ext):

    original.seek(0)  # http://code.djangoproject.com/ticket/8222
    image = Image.open(original)

    # convert to RGB if necessary
    if image.mode not in ('L', 'RGB', 'RGBA'):
        image = image.convert('RGB')

    split = size['wxh'].split('x')
    wxh = (int(split[0]), int(split[1]))

    # 'crop'
    if 'resize' in size and size['resize'] == 'crop':
        resized = ImageOps.fit(image, wxh, Image.ANTIALIAS)
    # 'scale' default
    else:
        image.thumbnail(wxh, Image.ANTIALIAS)
        resized = image

    # PNG and GIF are the same, JPG is JPEG
    format = format_ext.upper()
    if format == 'JPG':
        format = 'JPEG'

    # http://www.pythonware.com/library/pil/handbook/format-jpeg.htm
    quality = THUMBS_QUALITY

    io = cStringIO.StringIO()
    resized.save(io, format, quality=quality)
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
    if not 'code' in size or not re.match('^[0-9a-z]+$', size['code']):
        raise SizeError('Valid code required, eg, small.')
    if not 'wxh' in size or not re.match('^\d+x\d+$', size['wxh']):
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
        super(ImageThumbsFieldFile, self).delete(save)

        logger.debug('delete %s' % self.name)
        if self.field.sizes:
            for size in self.field.sizes:
                size_name = determine_thumb(size, self.name)
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
