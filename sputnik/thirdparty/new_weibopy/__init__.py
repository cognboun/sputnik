
# Copyright 2009-2010 Joshua Roesslein
# See LICENSE for details.

"""
weibo API library
"""
__version__ = '1.5'
__author__ = 'Joshua Roesslein'
__license__ = 'MIT'

import sys
import os
from sputnik.thirdparty.weibopy.models import Status, User, DirectMessage, Friendship, SavedSearch, SearchResult, ModelFactory, IDSModel
from sputnik.thirdparty.weibopy.error import WeibopError
from sputnik.thirdparty.weibopy.api import API
from sputnik.thirdparty.weibopy.cache import Cache, MemoryCache, FileCache
from sputnik.thirdparty.weibopy.auth import BasicAuthHandler, OAuthHandler
from sputnik.thirdparty.weibopy.streaming import Stream, StreamListener
from sputnik.thirdparty.weibopy.cursor import Cursor

# Global, unauthenticated instance of API
api = API()

def debug(enable=True, level=1):

    import httplib
    httplib.HTTPConnection.debuglevel = level

