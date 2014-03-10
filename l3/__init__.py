from datetime import datetime
import hmac
from hashlib import sha1
import base64
import urllib2
import urllib
from xml.dom import minidom


class ForbiddenException(Exception):
    pass


def _convert(val):
    if isinstance(val, basestring):
        if val.isdigit():
            return int(val)
        try:
            return float(val)
        except:
            pass
    return val


class NodeTraverser(object):
    def __init__(self, node):
        self.node = node

    def keys(self):
        return self.node._attrs.keys()

    def children_keys(self):
        result = []
        for child in self.node.childNodes:
            result.append(child.tagName)
        return result

    @property
    def children(self):
        return [NodeTraverser(n) for n in self.node.childNodes]

    def getattribute(self, name):
        return self.node.getAttribute(name)

    def getnode(self, name):
        for child in self.node.childNodes:
            if child.tagName == name:
                return NodeTraverser(child)

    def __getattr__(self, name):
        if type(name) == int or name.isdigit():
            return self.children[int(name)]
        if self.node.hasAttribute(name):
            return self.getattribute(name)
        return self.getnode(name)

    __getitem__ = __getattr__

    @property
    def val(self):
        if self.node.nodeType == self.node.TEXT_NODE:
            return _convert(self.node.data)
        for node in self.node.childNodes:
            if node.nodeType == node.TEXT_NODE:
                return _convert(node.wholeText)
        return None

    def __unicode__(self):
        return "<%s>%s</%s>" % (self.node.tagName, self.val, self.node.tagName)
    __str__ = __unicode__
    __repr__ = __str__

    def html(self):
        return self.node.toxml()


class XMLWrapper(object):
    def __init__(self, xml):
        self.xml = xml
        self.dom = minidom.parseString(xml)
        setattr(self, self.dom.documentElement.tagName,
                NodeTraverser(self.dom.documentElement))


class Level3Service(object):
    """
    Parameters :
        key_id(required)
        secret(required)
        service_url : optional that defaults to https://ws.level3.com
        content_type : optional that defaults to text/xml
        resource : optional that defaults to /api/v1.0
        wrap : optional that defaults to True. Will wrap the results in a
               friendly class that allows you to easily retrieve the values
               from the xml(see example).

    Example Usages:

    >>> from level3 import Level3Service
    >>> service = Level3Service('<key id>', '<secret>')
    >>> result = service('rtm', '<access group>',
    ...             {'serviceType' : 'caching',
    ...              'accessGroupChildren' : 'false',
    ...              'geo' : 'none' })
    >>> result.accessGroup.missPerSecond.val
    50.67
    >>> result.accessGroup.metros[0].name
    Atlanta, GA
    >>> result.accessGroup.metros[0].region
    North America
    >>> result.accessGroup.metros[0].requestsPerSecond.val
    600.45
    """

    def __init__(self, key_id, secret, service_url="https://ws.level3.com",
                 content_type='text/xml', resource="v1.0", method="GET",
                 wrap=True):
        self.key_id = key_id
        self.secret = secret
        self.service_url = service_url.rstrip('/')
        self.content_type = content_type
        self.resource = resource.strip('/')
        self.method = method

        self.current_date = datetime.utcnow()
        self.wrap = wrap

    def gen_new_date(self):
        self.current_date = datetime.utcnow()

    @property
    def formatted_date(self):
        return self.current_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def generate_auth_string(self, path, http_method='GET'):
        authstring = "%s\n/%s\n%s\n%s\n" % (
            self.formatted_date,
            path,
            self.content_type,
            http_method
        )

        hash = hmac.new(self.secret.encode('ascii'),
                        authstring.encode('ascii'), sha1).digest()
        return "MPA %s:%s" % (self.key_id, base64.b64encode(hash))

    def invalidate(self, access_group, property_name, urls):
        paths = '\n'.join(['<path>%s</path>' % url for url in urls])
        return self('invalidations', access_group, http_method='POST',
                    post_data="""
<properties>
<property>
<name>%s</name>
<paths>
%s
</paths>
</property>
</properties>
""" % (property_name, paths))

    def __call__(self, method, access_group, options={}, post_data=None,
                 http_method='GET'):
        self.gen_new_date()
        path = '%s/%s/%s' % (method, self.resource, access_group)
        url = '%s/%s' % (self.service_url, path)

        if options:
            encoded = urllib.urlencode(options)
            url += '?' + encoded

        headers = {
            'Date': self.formatted_date,
            'Authorization': self.generate_auth_string(path, http_method),
            'Content-Type': self.content_type
        }

        req = urllib2.Request(url, headers=headers)

        if post_data:
            req.add_data(post_data)

        try:
            result = urllib2.urlopen(req)
        except urllib2.HTTPError, ex:
            if hasattr(ex, 'getcode') and ex.getcode() == 403:
                raise ForbiddenException(
                    "something went wrong authorizing this request. %s" % (
                        str(ex.readlines())))
            else:
                raise Exception("There was an erorr %s" % str(ex.readlines()))

        data = result.read()
        if self.wrap:
            data = XMLWrapper(data)
        return data
