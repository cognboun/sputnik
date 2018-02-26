#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-12-19
# 
# Sputnik Cache Manager
# unthread-safe
#
# ToDoList:
# 

import types
import inspect
import functools
from SpuLogging import SpuLogging
from SpuCache import SpuCreateCache
from SpuCacheMonitor import SpuCacheMonitor, SpuCacheMMConsumer
from SpuDebug import *

"""
usage:

global SpuCacheManager instance:
from SpuCacheManager import cache

cache.set_value
cache.get_value
cache.remove

new SpuCacheManager instance:
from SpuCacheManager import SpuCacheManager
cache = SpuCacheManager(True)

"""

#
# Thrift serialize and deserialize
#
from thrift.TSerialization import serialize, deserialize


_logging = SpuLogging(module_name='SpuCacheManager')

def check_use_cache(func):
    def w(self, *args, **kwargs):
        if not self._use_cache or not SpuCacheManager._c_use_cache:
            return None

        return func(self, *args, **kwargs)
    return w


class SpuCacheManager:
    _c_conf = None
    _c_debug = False
    _c_instace = None
    _c_request_cache_enabled = False
    _c_use_cache = True
    _c_reset_cache = False

    _c_cache_monitor = None
    _c_remove_cache_type = []

    ProcessCache = 0
    LocalCache = 1
    GlobalCache = 2

    _c_cache = [
        [None, 'ProcessCache', ProcessCache],
        [None, 'LocalCache', LocalCache],
        [None, 'GlobalCache', GlobalCache]
        ]

    @classmethod
    def setting(cls, conf, debug):
        cls._c_conf = conf
        cls._c_debug = debug
        g_conf = conf.get('global', None)
        if g_conf:
            cache = SpuCreateCache(g_conf, 'global').create()
            if cache:
                cls._c_cache[2][0] = cache
                _logging.spu_debug('Enable global cache')
        l_conf = conf.get('local', None)
        if l_conf:
            cache = SpuCreateCache(l_conf, 'local').create()
            if cache:
                cls._c_cache[1][0] = cache
                _logging.spu_debug('Enable local cache')
        p_conf = conf.get('process', None)
        if p_conf:
            cache = SpuCreateCache(p_conf, 'process').create()
            if cache:
                cls._c_cache[0][0] = cache
                _logging.spu_debug('Enable process cache')

        cache_monitor_conf = conf.get('cache_monitor', False)
        if cache_monitor_conf:
            cls.start_cache_monitor(cache_monitor_conf)

    @classmethod
    def start_cache_monitor(cls, conf):
        enable = conf.get('enable', False)
        if not enable:
            return
        mq_addr = conf.get('mq_addr', None)
        pub_addr = conf.get('pub_addr', None)
        assert mq_addr and pub_addr, 'mq_addr or pub_addr is None'

        cache_type_list = []
        for cache_type in conf.get('remove_cache_type', []):
            for cache_t in cls._c_cache:
                if cache_type == cache_t[1]:
                    cache_type_list.append(cache_t[2])
        cls._c_remove_cache_type = cache_type_list

        cache_mm_consumer = SpuCacheMMConsumer(pub_addr, fcache)
        cls._c_cache_monitor = SpuCacheMonitor(mq_addr, cache_mm_consumer)
        cls._c_cache_monitor.start_monitor_thread()

    @classmethod
    def global_no_use_cache(cls):
        cls._c_use_cache = False

    @classmethod
    def global_use_cache(cls):
        cls._c_use_cache = True

    @classmethod
    def global_reset_cache(cls):
        cls._c_reset_cache = True

    @classmethod
    def global_no_reset_cache(cls):
        cls._c_reset_cache = False

    @classmethod
    def remove_cache_event(cls, key):
        """
        broadcast to cache cluster, except global
        global remove from sponsor
        TODO: A machine, a process execute remove local cache
        """
        if cls._c_cache_monitor:
            if cls.ProcessCache in cls._c_remove_cache_type:
                cls._c_cache_monitor.remove_process_cache_event(key)
            if cls.LocalCache in cls._c_remove_cache_type:
                cls._c_cache_monitor.remove_local_cache_event(key)

    @classmethod
    def remove_by_keyrule_cache_event(cls, key):
        """
        like remove_cache_event
        """
        if cls._c_cache_monitor:
            if cls.ProcessCache in cls._c_remove_cache_type:
                cls._c_cache_monitor.remove_by_keyrule_process_cache_event(key)
            if cls.LocalCache in cls._c_remove_cache_type:
                cls._c_cache_monitor.remove_by_keyrule_local_cache_event(key)

    @classmethod
    def remove_all_cache_event(cls):
        """
        like remove_cache_event
        """
        if cls._c_cache_monitor:
            if cls.ProcessCache in cls._c_remove_cache_type:
                cls._c_cache_monitor.remove_all_process_cache_event()
            if cls.LocalCache in cls._c_remove_cache_type:
                cls._c_cache_monitor.remove_all_local_cache_event()

    def __init__(self, use_cache):
        self._debug_time = SpuDebugTime()
        self._use_cache = use_cache

    def use_cache(self):
        return self._use_cache

    def iteration_cache(self, op, func, cache_type,
                        TType, **kwargs):
        cache_list = []
        for idx, (cache, name, cache_type_) in enumerate(self._c_cache):
            if cache and (not cache_type or cache_type == cache_type_):
                with self._debug_time:
                    (value, _return) = func(self, cache, cache_type_, TType, **kwargs)
                v = kwargs['value'] if 'value' in kwargs else value
                _logging.flowpath_cache(op, kwargs['key'], v, name,
                                        perf_t=self._debug_time.use_time)

                if cache_type != None:
                    return value

                # run on *get* method, set no return value
                if _return:
                    if cache_list:
                        # move cache
                        expire = 600
                        key = kwargs['key']
                        extime = cache.ttl(key)
                        if extime > 0:
                            expire = extime
                        for c, name, cache_type_ in cache_list:
                            cache_value = value
                            with self._debug_time:
                                if cache_type_ != self.ProcessCache and TType:
                                    cache_value = serialize(value)
                                c.set_value(key, value, expire=expire)
                            _logging.flowpath_cache('|-set(expire:%s)' % expire,
                                                    key, value,
                                                    name,
                                                    perf_t=self._debug_time.use_time)
                    return value
                cache_list.append((cache, name, cache_type_))
        return None

    @check_use_cache
    def set_value(self, key, value, expire=0,
                  cache_type=None, TType=None, cache_event=True):
        """
        cache_type: only use ProcessCache or LocalCache or GlobalCache
        cache_event: trigger cache event
        """
        
        def _func(self, cache, cache_type, TType, key, value, expire):
            if cache_type != self.ProcessCache and TType:
                value = serialize(value)
            cache.set_value(key, value, expire=expire)
            return (None, False)

        self.iteration_cache('set(expire:%s)' % expire, _func, cache_type,
                             TType=TType,
                             key=key, value=value,
                             expire=expire)

        # global reset model
        # remove all application instance process cache key
        if SpuCacheManager._c_reset_cache and cache_event:
            _logging.debug('set_value send remove_cache_event')
            SpuCacheManager.remove_cache_event(key)            

    @check_use_cache
    def get_value(self, key, cache_type=None, TType=None):
        if SpuCacheManager._c_reset_cache:
            return None

        def _func(self, cache, cache_type, TType, key):
            value = cache.get_value(key)
            if value and cache_type != self.ProcessCache and TType:
                value = deserialize(TType(), value)
            _exit = True if value != None else False
            return (value, _exit)
        
        return self.iteration_cache('get', _func, cache_type,
                                    TType=TType, key=key)

    @check_use_cache
    def remove(self, key, cache_type=None, cache_event=True):

        def _func(self, cache, cache_type, TType, key):
            cache.remove(key)
            return (None, False)

        self.iteration_cache('remove', _func, cache_type,
                             TType=None, key=key)

        if cache_event:
            _logging.debug('remove send remove_cache_event')
            SpuCacheManager.remove_cache_event(key)

    @check_use_cache
    def remove_by_keyrule(self, key, cache_type=None, cache_event=True):

        def _func(self, cache, cache_type, TType, key):
            cache.remove_by_keyrule(key)
            return (None, False)

        self.iteration_cache('remove_by_keyrule', _func, cache_type,
                             TType=None, key=key)

        if cache_event:
            _logging.debug('remove_by_keyrule send remove_by_keyrule_cache_event')
            SpuCacheManager.remove_by_keyrule_cache_event(key)

    @check_use_cache
    def remove_all(self, cache_type=None, cache_event=True):

        def _func(self, cache, cache_type, TType, key):
            cache.remove_all()
            return (None, False)

        self.iteration_cache('remove_all', _func, cache_type,
                             TType=None, key=None)

        if cache_event:
            _logging.debug('remove_all send remove_all_cache_event')
            SpuCacheManager.remove_all_cache_event()

#
# Function Cache
# fast cache
# **pure function** use fcache_add
# **side-effecting** use fcache_del or fcache_reset
#

base_type = (str, unicode, \
             int, float, long, bool, \
             list, dict, tuple, types.NoneType, \
             types.ComplexType)

def _is_base_type(value):
    return type(value) in base_type

def _get_primary_value(primary_key, *args, **kwargs):
    if type(primary_key) is not list:
        primary_key = [primary_key]

    value_list = []
    for pk in primary_key:
        if type(pk) is int:
            value_list.append(str(args[pk]))
        else:
            value_list.append(str(kwargs[pk]))
    return '(%s)' % '_'.join(value_list)

def fcache_default_key(func_name, primary_key, *args, **kwargs):
    """
    primary_key : args index or kwargs key

    default fcache key format:
    funcname_primaryvalue__args1value_args2value_kwargs1value_kwargs2value
    """
    primary_value = _get_primary_value(primary_key, *args, **kwargs)

    ks = []
    # remove self
    args = args if _is_base_type(args[0]) else args[1:]
    for arg in args:
        assert _is_base_type(arg), 'fcache_default_key argument type need in %s ' \
               'error type (%s:%s)' % (base_type, arg, type(arg))
        ks.append(str(arg))
    for k, v in kwargs.items():
        assert _is_base_type(v), 'fcache_default_key argument type need in %s ' \
               'error type (%s:%s)' % (base_type, v, type(v))
        ks.append('%s' % str(v))
    arg_value = '_'.join(ks)

    return '%s_%s__%s' % (func_name, primary_value, arg_value)

def fcache_get_default_args_by_key(key):
    pass

def fcache_default_get_key_family(func_name, primary_value):
    """
    find order: global > local > process
    """
    key_rule = '%s_%s__*' % (func_name, primary_value)
    cache_list = SpuCacheManager._c_cache[::-1]
    for (cache, name, cache_type) in cache_list:
        if cache:
            keys = cache.keys(key_rule)
            _logging.debug('find key family use key_rule:%s cache:%s keys:%s',
                           key_rule, name, keys)
            return keys
    return []

fcache = SpuCacheManager(True)
fcache_default_cache_type = None
def fcache_add(key_func=None, primary_key=None, expire=0, TType=None,
               cache_type=fcache_default_cache_type):
    """
    primary_key : args index(start on 0) or kwargs key
    TType       : Thrift Type Object
    nocache     : set nocache argument, no use cache
    cache_reset : set cache_reset argument, real call function and set cache
    """
    def _wrapper(self, func=None):
        if inspect.isfunction(self):
            func = self

        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            # set nocache argument no use cache
            nocache = kwargs.get('nocache', False)
            if 'nocache' in kwargs:
                del kwargs['nocache']
            if nocache:
                return func(*args, **kwargs)

            # set cache_reset argument
            cache_reset = kwargs.get('cache_reset', False)
            if 'cache_reset' in kwargs:
                del kwargs['cache_reset']

            assert key_func or primary_key, 'key_func and primary_key is None'

            # make cache key
            key = func.__name__
            if key_func:
                key = key_func(func, *args, **kwargs)
            else:
                key = fcache_default_key(key, primary_key,
                                         *args, **kwargs)
            # use cache
            if not cache_reset:
                value = fcache.get_value(key, TType=TType, cache_type=cache_type)
                if value:
                    return value

            # reset or cache miss, real call function and set cache
            value = func(*args, **kwargs)
            fcache.set_value(key, value, TType=TType,
                             expire=expire, cache_type=cache_type)

            # reset action and no global reset
            # on global reset, set_value send global remove_cache_event
            # remove all application instance process cache key
            if cache_reset and not SpuCacheManager._c_reset_cache:
                _logging.debug('fcache_add send remove_cache_event')
                SpuCacheManager.remove_cache_event(key)

            return value
        return func_wrapper
    return _wrapper

def fcache_remove(original_func=None, key_func=None, primary_key=None,
                  cache_type=fcache_default_cache_type):
    """
    remove key family
    """
    def _wrapper(func):
        assert key_func or (original_func and primary_key), \
               'key_func and original_func or primary_key is None'

        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if key_func:
                keys = key_func(original_func, *args, **kwargs)
                fcache_remove_by_keys(keys,
                                      cache_type=cache_type)
            else:
                kwargs['cache_type'] = cache_type
                fcache_remove_by_func(original_func, primary_key,
                                      *args, **kwargs)
            return result
        return func_wrapper
    return _wrapper

def fcache_no_cache(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        return nocache_call(func, *args, **kwargs)
    return func_wrapper

def fcache_reset_cache(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        return resetcache_call(func, *args, **kwargs)
    return func_wrapper

# fcache function

def fcache_remove_by_func(func, primary_key, *args, **kwargs):
    """
    remove key family
    func : original function
    """
    primary_value = _get_primary_value(primary_key,
                                       *args, **kwargs)
    cache_type = kwargs.get('cache_type', fcache_default_cache_type)
    keys = fcache_default_get_key_family(func.__name__, primary_value)
    for key in keys:
        fcache.remove(key, cache_type=cache_type)
    _logging.debug('fcache_remove_by_func func:%s primary_value:%s keys:%s' %
                   (func.__name__, primary_value, keys))

def fcache_remove_by_keys(keys, cache_type=fcache_default_cache_type):
    del_keys = []
    if type(keys) is not list:
        keys = [keys]
    for key in keys:
        del_keys.append(key)
        fcache.remove(key, cache_type=cache_type)
    _logging.debug('fcache_remove_by_keys keys:%s' % del_keys)

def fcache_batch_remove(func, key):
    pass

# cache function

class GlobalNotUseCache(object):
    def __init__(self):
        pass

    def __enter__(self):
        self._cache_state = SpuCacheManager._c_use_cache
        SpuCacheManager.global_no_use_cache()
        _logging.debug('Enter GlobalNotUseCache')

    def __exit__(self, exc_type, exc_value, exc_tb):
        SpuCacheManager._c_use_cache = self._cache_state
        _logging.debug('Exit GlobalNotUseCache exc_type:%s exc_value:%s exc_tb:%s',
                       exc_type, exc_value, exc_tb)
        if exc_tb:
            return False
        return True

class GlobalResetCache(object):
    def __init__(self):
        pass

    def __enter__(self):
        self._cache_state = SpuCacheManager._c_reset_cache
        SpuCacheManager.global_reset_cache()
        _logging.debug('Enter GlobalResetCache')

    def __exit__(self, exc_type, exc_value, exc_tb):
        SpuCacheManager._c_reset_cache = self._cache_state
        _logging.debug('Exit GlobalResetCache exc_type:%s exc_value:%s exc_tb:%s',
                       exc_type, exc_value, exc_tb)
        if exc_tb:
            return False
        return True

def nocache_call(fn, *args, **kwargs):
    cache_state = SpuCacheManager._c_use_cache
    SpuCacheManager.global_no_use_cache()
    _logging.debug('Enter nocache call')

    r = fn(*args, **kwargs)

    SpuCacheManager._c_use_cache = cache_state
    _logging.debug('Exit nocall call')        
    return r

def resetcache_call(fn, *args, **kwargs):
    cache_state = SpuCacheManager._c_reset_cache    
    SpuCacheManager.global_reset_cache()
    _logging.debug('Enter resetcache call')

    r = fn(*args, **kwargs)

    SpuCacheManager._c_reset_cache = cache_state    
    _logging.debug('Exit resetcall call')        
    return r

cache = SpuCacheManager(True)
