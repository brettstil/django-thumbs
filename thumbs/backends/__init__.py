
# https://github.com/duointeractive/django-athumb

from storages.backends.s3boto import S3BotoStorage


class PublicS3BotoStorage(S3BotoStorage):
    """
Same as S3BotoStorage, but defaults to uploading everything with a
public acl.

Since we don't have to hit S3 for auth keys, this backend is much
faster than S3BotoStorage, as it makes no attempt to validate whether
keys exist.

WARNING: This backend makes absolutely no attempt to verify whether the
given key exists on self.url(). This is much faster, but be aware.
"""
    def __init__(self, *args, **kwargs):
        super(PublicS3BotoStorage, self).__init__(
            # AWS_DEFAULT_ACL
            acl='public-read',
            # AWS_QUERYSTRING_AUTH
            querystring_auth=False,
            # AWS_QUERYSTRING_EXPIRE
            querystring_expire=False,
            *args, **kwargs)

    def url(self, name):
        """
Since we assume all public storage with no authorization keys, we can
just simply dump out a URL rather than having to query S3 for new keys.
"""
        name = self._clean_name(name)
        # AWS_S3_SECURE_URLS
        scheme = 'https' if self.secure_urls else 'http'
        # AWS_S3_CUSTOM_DOMAIN
        if self.custom_domain:
            return '%s://%s/%s' % (scheme, self.custom_domain, name)
        return '%s://s3.amazonaws.com/%s/%s' % (scheme, self.bucket_name, name)
