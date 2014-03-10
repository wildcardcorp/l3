Introduction
============

This package provides basic support for invalidating urls with level3 CDN.

Example::

    import l3
    service = l3.Level3Service(key_id, secret)
    service.invalidate(access_group, 'www.mysite.com', ['/', '/otherpath'])
