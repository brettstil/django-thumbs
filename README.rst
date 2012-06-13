=============
django-thumbs
=============

The easiest way to create thumbnails for your images with Django. Works with any storage backend.


Features
========

* Easy to integrate in your code (no database changes, works as an ``ImageField``)
* Works with any storage backend
* Generates thumbnails after image is uploaded into memory
* Deletes thumbnails when the image file is deleted
* Provides easy access to the thumbnails' URLs (similar method as with ``ImageField``)


Installation
============

Install django-thumbs into a virtualenv using pip::

    (env)$ pip install -e git+https://github.com/brettstil/django-thumbs.git#egg=django-thumbs

Add ``thumbs`` to your installed apps::

    INSTALLED_APPS = (
        # ...
        'thumbs',
    )

Setup
=====

* Import it in your models.py and replace ``ImageField`` with ``ImageThumbsField`` in your model
* Add a ``sizes`` attribute with a list of sizes you want to use for the thumbnails
* Make sure you have defined ``STATIC_URL`` in your settings.py
* That's it!


Working example
===============

::

    from django.db import models
    from thumbs.fields import ImageThumbsField

    class Person(models.Model):
        photo = ImageThumbsField(upload_to='images', sizes=((125,125),(200,200)))
        second_photo = ImageThumbsField(upload_to='images')

In this example we have a ``Person`` model with 2 image fields.

You can see the field ``second_photo`` doesn't have a ``sizes`` attribute. This field works exactly the same way as a normal ``ImageField``.

The field ``photo`` has a ``sizes`` attribute specifying desired sizes for the thumbnails. This field works the same way as ``ImageField`` but it also creates the desired thumbnails when uploading a new file and deletes the thumbnails when deleting the file.

With ``ImageField`` you retrieve the URL for the image with: ``someone.photo.url`` With ``ImageThumbsField`` you retrieve it the same way. You also retrieve the URL for every thumbnail specifying its size: In this example we use ``someone.photo.url_125x125`` and ``someone.photo.url_200x200`` to get the URL of both thumbnails.


Uninstall
=========

At any time you can go back and use ``ImageField`` again without altering the database or anything else. Just replace ``ImageThumbsField`` with ``ImageField`` again and make sure you delete the ``sizes`` attribute. Everything will work the same way it worked before using django-thumbs. Just remember to delete generated thumbnails in the case you don't want to have them anymore.

