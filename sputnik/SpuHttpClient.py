# -*- coding: utf-8 -*-

import os
import httplib
import logging
import mimetools
import mimetypes
from SpuDebug import *
from SpuUtil import *
from urllib import urlencode
import tornado.httpclient as httpclient

def http_get_response(url, time_out = None):
    r = ''
    GDebugTime.start()
    http_client = httpclient.HTTPClient()
    try:
        response = None
        if time_out == None:
            response = http_client.fetch(url)
        else:
            req = httpclient.HTTPRequest(url, request_timeout=time_out)
            response = http_client.fetch(req)
        r = response
    except httpclient.HTTPError as e:
        logging.debug('Http Error: %s' % e)
        return e
    GDebugTime.set_function('http_get')
    GDebugTime.point(to_unicode(url))
    return r

def http_get(url, time_out = None):
    response = http_get_response(url, time_out)
    if isinstance(response, Exception):
        return response
    else:
        return response.body

def http_post(url, data, files = None):
    r = ''
    request = make_post_request(url, data = data, files = files)
    http_client = httpclient.HTTPClient()
    try:
        response = http_client.fetch(request)
        r = response.body
    except httpclient.HTTPError, e:
        logging.debug(e)
    return r

def list_unique(l):
    return list(set(l))

def _encode(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')
    else:
        return s

def make_qs(query_args):
    kv_pairs = []
    for (key, val) in query_args.iteritems():
        if val:
            if isinstance(val, list):
                for v in val:
                    kv_pairs.append((key, _encode(v)))
            else:
                kv_pairs.append((key, _encode(val)))

    qs = urlencode(kv_pairs)

    return qs

def make_url(base, **query_args):
    ''' 
    построить URL из базового урла и набора CGI-параметров
    параметры с пустым значением пропускаются, удобно для последовательности:
    make_url(base, hhtoken=request.cookies.get('hhtoken'))
    '''
    qs = make_qs(query_args)

    if qs:
        return base + '?' + qs
    else:
        return base 

def get_all_files(root, extension=None):
    out = list()
    for subdir, dirs, files in os.walk(root):
        out += [os.path.abspath(file) for file in files if extension and file.endswith(extension)]
    return out

from copy import copy

def dict_concat(dict1, dict2):
    """
    Returns content of dict1 after dict1.update(dict2)? without its modification
    """
    dict3 = copy(dict1)
    dict3.update(dict2)
    return dict3


ENCODE_TEMPLATE= '--%(boundary)s\r\nContent-Disposition: form-data; name=%(name)s\r\n\r\n%(data)s\r\n'
ENCODE_TEMPLATE_FILE = '--%(boundary)s\r\nContent-Disposition: form-data; name="%(name)s"; filename="%(filename)s"\r\nContent-Type: %(contenttype)s\r\n\r\n%(data)s\r\n'

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def make_mfd(fields, files):
    ''' 
    Constructs request body in multipart/form-data format

    fields :: { field_name : field_value }
    files :: { field_name: [{ "filename" : fn, "body" : bytes }]}
    '''

    BOUNDARY = mimetools.choose_boundary()
    body = ""

    for name, data in fields.iteritems():

        if not data:
            continue

        if isinstance(data, list):
            for value in data:
                body += ENCODE_TEMPLATE % {
                            'boundary': BOUNDARY,
                            'name': str(name),
                            'data': _encode(value)
                        }
        else:
            body += ENCODE_TEMPLATE % {
                        'boundary': BOUNDARY,
                        'name': str(name),
                        'data': _encode(data)
                    }

    for name, files in files.iteritems():
        for file in files:
            body += ENCODE_TEMPLATE_FILE % {
                        'boundary': BOUNDARY,
                        'data': file["body"],
                        'name': name,
                        'filename': _encode(file["filename"]),
                        'contenttype': str(get_content_type(file["filename"]))
                    }

    body += '--%s--\r\n' % BOUNDARY
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return body, content_type


def make_get_request(url, data={}, headers={}, connect_timeout=0.5, request_timeout=2):
    return tornado.httpclient.HTTPRequest(
                    url=make_url(url, **data),
                    headers=headers,
                    connect_timeout=connect_timeout,
                    request_timeout=request_timeout)


def make_post_request(url, data={}, headers={}, files={},
        connect_timeout=0.5, request_timeout=2):

    if files:
        body, content_type = make_mfd(data, files)
    else:
        body = make_qs(data)
        content_type = 'application/x-www-form-urlencoded'

    headers.update({'Content-Type' : content_type,
               'Content-Length': str(len(body))})

    return httpclient.HTTPRequest(
                method='POST',
                headers=headers,
                url=url,
                body=body,
                connect_timeout=connect_timeout,
                request_timeout=request_timeout)


def make_put_request(url, data={}, headers={}, body="", connect_timeout=0.5, request_timeout=2):
    return tornado.httpclient.HTTPRequest(
                    url=make_url(url, **data),
                    method='PUT',
                    headers=headers,
                    body=body,
                    connect_timeout=connect_timeout,
                    request_timeout=request_timeout)


def make_delete_request(url, data={}, headers={}, connect_timeout=0.5, request_timeout=2):
    return tornado.httpclient.HTTPRequest(
                    url=make_url(url, **data),
                    method='DELETE',
                    headers=headers,
                    connect_timeout=connect_timeout,
                    request_timeout=request_timeout)


def _asciify_url_char(c):
    if ord(c) > 127:
        return hex(ord(c)).replace('0x', '%')
    else:
        return c

def asciify_url(url):
    return ''.join(map(_asciify_url_char, url))
