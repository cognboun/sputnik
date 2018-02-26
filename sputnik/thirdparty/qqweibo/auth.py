#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2009-2010 Joshua Roesslein
# Copyright 2011 andelf <andelf@gmail.com>
# See LICENSE for details.
# Time-stamp: <2011-06-04 08:14:39 andelf>

from sputnik.thirdparty.qqweibo.compat import Request, urlopen
from sputnik.thirdparty.qqweibo import oauth
from sputnik.thirdparty.qqweibo.error import QWeiboError
from sputnik.thirdparty.qqweibo.api import API


class AuthHandler(object):

    def apply_auth_headers(self, url, method, headers, parameters):
        """Apply authentication headers to request"""
        raise NotImplementedError

    def get_username(self):
        """Return the username of the authenticated user"""
        raise NotImplementedError

    def get_signed_url(self, url, method, headers, parameters):
        raise NotImplementedError


class OAuthHandler(AuthHandler):
    """OAuth authentication handler"""

    OAUTH_HOST = 'graph.qq.com'
    OAUTH_ROOT = '/oauth2.0/'

    def __init__(self, consumer_key, consumer_secret, callback=None):
        #self._consumer = oauth.OAuthConsumer(consumer_key, consumer_secret)
        self._consumer = consumer_key
        self._sigmethod = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.request_token = None
        self.access_token = None
        self.callback = callback or 'null'  # fixed
        self.username = None

    def _get_oauth_url(self, endpoint):
        if endpoint in ('token', 'authorize'):
            prefix = 'https://'
        else:
            prefix = 'http://'
        return prefix + self.OAUTH_HOST + self.OAUTH_ROOT + endpoint

    def apply_auth_headers(self, url, method, headers, parameters):
        """applay auth to request headers
        QQ weibo doesn't support it.
        """
        request = oauth.OAuthRequest.from_consumer_and_token(
            self._consumer, http_url=url, http_method=method,
            token=self.access_token, parameters=parameters
        )
        request.sign_request(self._sigmethod, self._consumer, self.access_token)
        headers.update(request.to_header())

    def get_signed_url(self, url, method, headers, parameters):
        """only sign url, no authentication"""
        # OAuthRequest(http_method, http_url, parameters)
        request = oauth.OAuthRequest(http_method=method, http_url=url, parameters=parameters)
        request.sign_request(self._sigmethod, self._consumer, self.access_token)
        return request.to_url()

    def get_authed_url(self, url, method, headers, parameters):
        """auth + sign"""
        request = oauth.OAuthRequest.from_consumer_and_token(
            self._consumer, http_url=url, http_method=method,
            token=self.access_token, parameters=parameters
        )
        request.sign_request(self._sigmethod, self._consumer, self.access_token)
        return request.to_url()

    def _get_request_token(self):
        try:
            url = self._get_oauth_url('authorize')
            print url
            print self.callback

            request = oauth.OAuthRequest.from_consumer_and_token(
                self._consumer, http_url=url, callback=self.callback
            )
            request.sign_request(self._sigmethod, self._consumer, None)
            return request.to_url()
            print request.to_url()
            resp = urlopen(Request(request.to_url()))  # must
            print "ddd", resp.read()
            return oauth.OAuthToken.from_string(resp.read().decode('ascii'))
        except RuntimeError as e:
            raise QWeiboError(e)

    def set_request_token(self, key, secret):
        self.request_token = oauth.OAuthToken(key, secret)

    def set_access_token(self, key, secret):
        self.access_token = oauth.OAuthToken(key, secret)

    def get_authorization_url(self, signin_with_weibo=False):
        """Get the authorization URL to redirect the user"""
        try:
            # get the request token
            return self._get_request_token() 
            self.request_token = self._get_request_token()
            
            # build auth request and return as url
            if signin_with_weibo:
                url = self._get_oauth_url('authenticate')
            else:
                url = self._get_oauth_url('authorize')
            request = oauth.OAuthRequest.from_token_and_callback(
                token=self.request_token, http_url=url, callback=self.callback
            )

            return request.to_url()
        except RuntimeError as e:
            raise QWeiboError(e)

    def get_access_token(self, verifier=None):
        """
        After user has authorized the request token, get access token
        with user supplied verifier.
        """
        try:
            url = self._get_oauth_url('access_token')

            # build request
            request = oauth.OAuthRequest.from_consumer_and_token(
                self._consumer,
                token=self.request_token, http_url=url,
                verifier=str(verifier)
            )
            request.sign_request(self._sigmethod, self._consumer, self.request_token)

            # send request
            resp = urlopen(Request(request.to_url()))  # must
            self.access_token = oauth.OAuthToken.from_string(resp.read().decode('ascii'))

            #print ('Access token key: ' + str(self.access_token.key))
            #print ('Access token secret: ' + str(self.access_token.secret))

            return self.access_token
        except Exception as e:
            raise QWeiboError(e)

    def setToken(self, token, tokenSecret):
        self.access_token = oauth.OAuthToken(token, tokenSecret)

    def get_username(self):
        if self.username is None:
            api = API(self)
            user = api.user.info()
            if user:
                self.username = user.name
            else:
                raise QWeiboError("Unable to get username, invalid oauth token!")
        return self.username
