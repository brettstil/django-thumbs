
# django-thumbs

Create thumbnails for your images with Django.

## Fork

Forked from <https://code.google.com/p/django-thumbs/>.

## Features

* Easy to integrate in your code (no database changes, works as an `ImageField`)
* Works with any storage backend
* Generates thumbnails after image is uploaded into memory
* Deletes thumbnails when the image file is deleted
* Provides easy access to the thumbnails' URLs (similar method as with `ImageField`)

## Example

    from django.db import models
    from thumbs.fields import ImageThumbsField

    class Person(models.Model):

        SIZES = (
            {'code': 'avatar', 'wxh': '125x125', 'resize': 'crop'},
            {'code': 'm', 'wxh': '640x480', 'resize': 'scale'},
            {'code': '150', 'wxh': '150x150'},  # 'resize' defaults to 'scale'
        )
        photo = ImageThumbsField(upload_to='images', sizes=SIZES)

The field `photo` has a `sizes` attribute specifying desired sizes for the thumbnails. This field works the same way as `ImageField` but it also creates the desired thumbnails when uploading a new file and deletes the thumbnails when deleting the file.

With `ImageThumbsField` you retrieve the URL for every thumbnail specifying its size code.  In this example we use `someone.photo.url_avatar`, `someone.photo.url_150` or `someone.photo.url_m` to get the thumbnail URL.

## Install

Install django-thumbs into a virtualenv using pip:

    (env)$ pip install -e git+https://github.com/brettstil/django-thumbs.git#egg=django-thumbs

Add `thumbs` to your installed apps:

    INSTALLED_APPS = (
        # ...
        'thumbs',
    )

## Usage

* Import it in your `models.py` and replace `ImageField` with `ImageThumbsField` in your model
* Add a `sizes` attribute with a list of sizes you want to use for the thumbnails
* Make sure you have defined `STATIC_URL` in your settings.py

## Sizes

Each size is a dictionary that defines a thumbnail.  For example,

    SIZES = (
        {'code': 'avatar', 'wxh': '125x125', 'resize': 'crop'},
        {'code': 'm', 'wxh': '640x480', 'resize': 'scale'},
        {'code': '150', 'wxh': '150x150'},  # 'resize' defaults to 'scale'
    )

Size validation errors will raise `SizeError`.

### code (required)

matches re: `^[0-9a-z]+$`

`code` is the size name.  It appears in the thumb filename separated by `THUMBS_DELIMITER`.  For example, `'original.jpg'` becomes `'original-small.jpg'` for the default delimiter `'-'` and code `'small'`.

### wxh (required)

matches re: `^\d+x\d+$`

`wxh` is the width x height as a string.

### resize (optional)

default: `'scale'`
options: `'scale'` or `'crop'`

`resize` determines how the image will be resized.

`'scale'` resizes the thumb to `wxh`.  For example, a 2000 x 1000 image will become 500 x 250 for `'scale'` and a `wxh` of `'500x500'`.  `'scale'` does not enlarge a photo.  A 200 x 100 image will remain 200 x 100 for `'scale'` and `wxh` of `'500x500'`.  `'scale'` does not crop.

`'crop'` crops and centers the image fit `wxh` exactly.  For example, a 2000 x 1000 image will become 500 x 500 for `'crop'` and a `wxh` of `'500x500'`.  `'crop'` will enlarge a photo to exactly fit `wxh`.  A 200 x 100 image will enlarge and crop to 500 x 500 for `'crop'` and `wxh` of `'500x500'`.

## Settings

`django-thumbs` will use default settings unless these settings are found in Django settings.

### THUMBS_DELIMITER

default: `'-'`

`THUMBS_DELIMITER` sets the delimiter between the original image base name and the thumb size `code`.  For example, `'original.jpg'` becomes `'original-small.jpg'` for the default delimiter `'-'` and code `'small'`.

### THUMBS_JPG

default: `False`

Set `THUMBS_JPG` to `True` to force all thumbnails to `.jpg` format and file extension regardless of original image format or file extension.

### THUMBS_QUALITY

default: `90`

`THUMBS_QUALITY` sets PIL quality.  See <http://www.pythonware.com/library/pil/handbook/format-jpeg.htm>

## PublicS3BotoStorage

`PublicS3BotoStorage` generates clean URLs for Amazon S3 in code--without calling Amazon and without S3 querystring auth and expires.  Hooray!  URLs are `'public-read'`.

`PublicS3BotoStorage` is based on `S3BotoStorage_AllPublic` from <https://github.com/duointeractive/django-athumb>.

Add to `requirements.txt`:

    django-storages==1.1.4
    boto==2.5.2

In Django settings, instead of

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

use `PublicS3BotoStorage`:

    DEFAULT_FILE_STORAGE = 'thumbs.backends.PublicS3BotoStorage'

`PublicS3BotoStorage` looks for `AWS_S3_SECURE_URLS` and `AWS_S3_CUSTOM_DOMAIN` settings.  `AWS_S3_SECURE_URLS` sets `https` or `http`.  `AWS_S3_CUSTOM_DOMAIN` sets custom domain or `s3.amazonaws.com`.

## Uninstall

At any time you can go back and use `ImageField` again without altering the database or anything else. Just replace `ImageThumbsField` with `ImageField` again and make sure you delete the `sizes` attribute. Everything will work the same way it worked before using django-thumbs. Just remember to delete generated thumbnails in the case you don't want to have them anymore.

