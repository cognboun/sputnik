#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-13
#
# Sputnik Session
#  Base Code on Django Session
# ToDoList:
# 

import redis
import base64
import os
import random
import sys
import time
from datetime import datetime, timedelta
try:
    import cPickle as pickle
except ImportError:
    import pickle

import SpuConfig
from SpuUtil import md5

# Use the system (hardware-based) random number generator if it exists.
if hasattr(random, 'SystemRandom'):
    randrange = random.SystemRandom().randrange
else:
    randrange = random.randrange
MAX_SESSION_KEY = 18446744073709551616L     # 2 << 63

engine_dict = {}

def register_session_engine(engine_name, engine):
    global engine_dict
    engine_dict[engine_name] = engine

def get_session_engine_class():
    session_config = SpuConfig.SpuSession_Config
    engine_class = engine_dict.get(session_config['session_engine'], default_engine)
    return engine_class

def get_session_engine(session_key = None):
    engine_class = get_session_engine_class()
    return engine_class(session_key)

class CreateError(Exception):
    """
    Used internally as a consistent exception type to catch from save (see the
    docstring for SessionBase.save() for details).
    """
    pass

class SpuSessionBase(object):
    """
    Base class for all Session classes.
    """
    TEST_COOKIE_NAME = 'testcookie'
    TEST_COOKIE_VALUE = 'worked'

    def __init__(self, session_key=None):
        session_config = SpuConfig.SpuSession_Config
        self._session_key = session_key
        self.permanent = session_config['session_permanent']
        self.accessed = False
        self.modified = False
        self.session_key_function = session_config['session_key_function']
        
    def __contains__(self, key):
        return key in self._session

    def __getitem__(self, key):
        return self._session[key]

    def __setitem__(self, key, value):
        self._session[key] = value
        self.modified = True

    def __delitem__(self, key):
        del self._session[key]
        self.modified = True

    def keys(self):
        return self._session.keys()

    def items(self):
        return self._session.items()

    def get(self, key, default=None):
        return self._session.get(key, default)

    def pop(self, key, *args):
        self.modified = self.modified or key in self._session
        return self._session.pop(key, *args)

    def setdefault(self, key, value):
        if key in self._session:
            return self._session[key]
        else:
            self.modified = True
            self._session[key] = value
            return value

    def set_test_cookie(self):
        self[self.TEST_COOKIE_NAME] = self.TEST_COOKIE_VALUE

    def test_cookie_worked(self):
        return self.get(self.TEST_COOKIE_NAME) == self.TEST_COOKIE_VALUE

    def delete_test_cookie(self):
        del self[self.TEST_COOKIE_NAME]

    def encode(self, session_dict):
        "Returns the given session dictionary pickled and encoded as a string."
        session_config = SpuConfig.SpuSession_Config
        pickled = pickle.dumps(session_dict, pickle.HIGHEST_PROTOCOL)
        pickled_md5 = md5(pickled + session_config['secret_key'])
        return base64.encodestring(pickled + pickled_md5)

    def decode(self, session_data):
        session_config = SpuConfig.SpuSession_Config
        encoded_data = base64.decodestring(session_data)
        pickled, tamper_check = encoded_data[:-32], encoded_data[-32:]
        if md5(pickled + session_config['secret_key']) != tamper_check:
            assert None, "User tampered with session cookie."
        try:
            return pickle.loads(pickled)
        # Unpickling can cause a variety of exceptions. If something happens,
        # just return an empty dictionary (an empty session).
        except:
            return {}

    def update(self, dict_):
        self._session.update(dict_)
        self.modified = True

    def has_key(self, key):
        return self._session.has_key(key)

    def values(self):
        return self._session.values()

    def iterkeys(self):
        return self._session.iterkeys()

    def itervalues(self):
        return self._session.itervalues()

    def iteritems(self):
        return self._session.iteritems()

    def clear(self):
        # To avoid unnecessary persistent storage accesses, we set up the
        # internals directly (loading data wastes time, since we are going to
        # set it to an empty dict anyway).
        self._session_cache = {}
        self.accessed = True
        self.modified = True

    def _get_new_session_key(self):
        "Returns session key that isn't being used."
        session_config = SpuConfig.SpuSession_Config
        # The random module is seeded when this Apache child is created.
        # Use session_config[secret_key] as added salt.
        if self.session_key_function:
            return self.session_key_function()
        try:
            pid = os.getpid()
        except AttributeError:
            # No getpid() in Jython, for example
            pid = 1
        while 1:
            session_key = md5("%s%s%s%s" % 
                              (randrange(0, MAX_SESSION_KEY),
                               pid,
                               time.time(),
                               session_config['secret_key']))

            if not self.exists(session_key):
                break
        return session_key

    def _get_session_key(self):
        if self._session_key:
            return self._session_key
        else:
            self._session_key = self._get_new_session_key()
            self.modified = True
            return self._session_key

    def _set_session_key(self, session_key):
        self._session_key = session_key

    session_key = property(_get_session_key, _set_session_key)

    def _get_session(self, no_load=False):
        """
        Lazily loads session from storage (unless "no_load" is True, when only
        an empty dict is stored) and stores it in the current instance.
        """
        self.accessed = True
        try:
            return self._session_cache
        except AttributeError:
            if self._session_key is None or no_load:
                self._session_cache = {}
            else:
                self._session_cache = self.load()
        return self._session_cache

    _session = property(_get_session)

    def get_expiry_age(self):
        """Get the number of seconds until the session expires."""
        session_config = SpuConfig.SpuSession_Config
        expiry = self.get('_session_expiry')
        if not expiry:   # Checks both None and 0 cases
            return session_config['session_cookie_age']
        if not isinstance(expiry, datetime):
            return expiry
        delta = expiry - datetime.now()
        return delta.days * 86400 + delta.seconds

    def get_expiry_date(self):
        """Get session the expiry date (as a datetime object)."""
        session_config = SpuConfig.SpuSession_Config
        expiry = self.get('_session_expiry')
        if isinstance(expiry, datetime):
            return expiry
        if not expiry:   # Checks both None and 0 cases
            expiry = session_config['session_cookie_age']
        return datetime.now() + timedelta(seconds=expiry)

    def set_expiry(self, value):
        """
        Sets a custom expiration for the session. ``value`` can be an integer,
        a Python ``datetime`` or ``timedelta`` object or ``None``.

        If ``value`` is an integer, the session will expire after that many
        seconds of inactivity. If set to ``0`` then the session will expire on
        browser close.

        If ``value`` is a ``datetime`` or ``timedelta`` object, the session
        will expire at that specific future time.

        If ``value`` is ``None``, the session uses the global session expiry
        policy.
        """
        if value is None:
            # Remove any custom expiration for this session.
            try:
                del self['_session_expiry']
            except KeyError:
                pass
            return
        if isinstance(value, timedelta):
            value = datetime.now() + value
        self['_session_expiry'] = value

    def get_expire_at_browser_close(self):
        """
        Returns ``True`` if the session is set to expire when the browser
        closes, and ``False`` if there's an expiry date. Use
        ``get_expiry_date()`` or ``get_expiry_age()`` to find the actual expiry
        date/age, if there is one.
        """
        session_config = SpuConfig.SpuSession_Config
        close = None
        if self.get('_session_expiry') is None:
            close = session_config['session_expire_at_browser_close']
        close = self.get('_session_expiry') == 0
        return close

    def flush(self):
        """
        Removes the current session data from the database and regenerates the
        key.
        """
        self.clear()
        self.delete()
        self.create()

    def cycle_key(self):
        """
        Creates a new session key, whilst retaining the current session data.
        """
        data = self._session_cache
        key = self.session_key
        self.create()
        self._session_cache = data
        self.delete(key)

    # Methods that child classes must implement.

    def exists(self, session_key):
        """
        Returns True if the given session_key already exists.
        """
        raise NotImplementedError

    def create(self):
        """
        Creates a new session instance. Guaranteed to create a new object with
        a unique key and will have saved the result once (with empty data)
        before the method returns.
        """
        raise NotImplementedError

    def save(self, must_create=False):
        """
        Saves the session data. If 'must_create' is True, a new session object
        is created (otherwise a CreateError exception is raised). Otherwise,
        save() can update an existing object with the same key.
        """
        raise NotImplementedError

    def delete(self, session_key=None):
        """
        Deletes the session data under this key. If the key is None, the
        current session key value is used.
        """
        raise NotImplementedError

    def load(self):
        """
        Loads the session data and returns a dictionary.
        """
        raise NotImplementedError

class SpuSessionRedis(SpuSessionBase):
    redis_s = None
    
    @classmethod
    def get_redis(cls, config):
        if not cls.redis_s:
            pool = redis.ConnectionPool(
                host = config['host'], 
                port = config['port'], 
                db = config['db'])
            cls.redis_s = redis.Redis(connection_pool=pool)
        return cls.redis_s

    def __init__(self, session_key = None):
        SpuSessionBase.__init__(self, session_key)
        session_config = SpuConfig.SpuSession_Config
        self._redis = SpuSessionRedis.get_redis(session_config['session_db_config'])

    def load(self):
        try:
            session_data = eval(self._redis.get(self.session_key))
        except Exception:
            session_data = None
        if session_data is not None:
            return session_data
        self.create()
        return {}

    def create(self):
        # Because a cache can fail silently (e.g. redis), we don't know if
        # we are failing to create a new session because of a key collision or
        # because the cache is missing. So we try for a (large) number of times
        # and then raise an exception. That's the risk you shoulder if using
        # cache backing.
        for i in xrange(10000):
            self.session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            return
        assert None, 'Unable to create a new session key.'

    def save(self, must_create=False):
        if must_create and self.exists(self.session_key):
            raise CreateError

        self._redis.set(self.session_key, self._get_session(no_load=must_create))
        if not self.permanent:
            self._redis.expire(self.session_key, self.get_expiry_age())

    def exists(self, session_key):
        return self._redis.exists(session_key)
    
    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self._session_key
        self._redis.delete(session_key)

register_session_engine('redis', SpuSessionRedis)
default_engine = engine_dict['redis']
