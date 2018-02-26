#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-9
#
# Sputnik Cache
#   把python对象转换成一个可以作为cache存储的value
# lru_list thread-safe
# ToDoList:
# 

import re
import time
import heapq
import redis
import threading
import SpuUtil as util
import SpuException

from SpuDebug import SpuDebugTime
from SpuLogging import SpuLogging


_logging = SpuLogging(module_name='SpuCache')

##
# Cache Exception
##
class UnknowCache(SpuException.SpuException):
    def __init__(self, cachename):
        self._cachename = cachename

    def __str__(self):
        return 'Unknow Cache (%s)' % self._cachename

class CacheCnfFailed(SpuException.SpuException):
    def __init__(self, cachecnf):
        self._cachecnf = cachecnf

    def __str__(self):
        str = ''
        if not self._cachecnf:
            str = 'Not cachecnf'
            return str
        if not self._dbcnf.get('type', None):
            str += 'Not type'
        return str

##
# Cache Factory
##
class SpuCreateCache:
    cache_type = {}

    @classmethod
    def register_cache(cls, _type, cache_class, policy='default'):
        policys = cls.cache_type.get(_type)
        if not policys:
            policys = {}
            cls.cache_type[_type] = policys
        policys[policy] = cache_class

    @classmethod
    def get_cacheclass(cls, type, policy='default'):
        return cls.cache_type[type][policy]

    def __init__(self, cachecnf, name=''):
        self._cachecnf = cachecnf
        self._name = name

    def create(self):
        if not self._cachecnf['enable']:
            return None

        try:
            _type = self._cachecnf['type']
            policy = self._cachecnf.get('policy', 'default')
            c = SpuCreateCache.get_cacheclass(_type, policy)
            _logging.debug('Create %s cache type:%s policy:%s' % (
                self._name,
                _type, policy))
        except Exception:
            raise CacheCnfFailed(self._cachecnf)

        cache = c(self._cachecnf)
        cache.connection()
        return cache

##
# Cache Base Class
##

def get_stat(get_func):
    def _f(self, key):
        cache_item = get_func(self, key)
        if cache_item:
            self.add_hit()
        else:
            self.add_miss()
        return cache_item
    return _f

_md5_key=lambda key: util.md5(key) if isinstance(key, basestring) else key
_default_key=lambda key: key
class SpuCacheBase(object):
    """
    Sputnik Cache Base Class
    """
    def __init__(self, cachecnf, key_type = ''):
        self._cachecnf = cachecnf
        self._key_type = key_type
        self._key = _md5_key if key_type == 'md5' else _default_key
        self._access = 0
        self._hit = 0
        self._miss = 0

    def set_keytype(self, _type):
        """key is 'md5' or ''"""
        self._key_type = _type

    def add_hit(self):
        self._access += 1
        self._hit += 1

    def add_miss(self):
        self._access += 1
        self._miss += 1

    def hit(self):
        return self._hit

    def miss(self):
        return self._miss

    def access(self):
        return self._access

    def connection(self):
        raise SpuException.NotImplInterface(self.__class__, 'connect')

    def close(self):
        raise SpuException.NotImplInterface(self.__class__, 'close')

    def set_value(self, key, value, expire=0):
        raise SpuException.NotImplInterface(self.__class__, 'set_value')

    def get_value(self, key):
        raise SpuException.NotImplInterface(self.__class__, 'get_value')

    def remove(self, key):
        raise SpuException.NotImplInterface(self.__class__, 'remove')

    def remove_by_keyrule(self, keyrule):
        keys = self.keys(keyrule)
        for key in keys:
            self.remove(key)

    def remove_all(self):
        raise SpuException.NotImplInterface(self.__class__, 'remove_all')

    def keys(self, key_rule):
        raise SpuException.NotImplInterface(self.__class__, 'keys')

    def cache_size(self):
        raise SpuException.NotImplInterface(self.__class__, 'cache_size')

    def get_all(self):
        raise SpuException.NotImplInterface(self.__class__, 'get_all')

    def expire(self, key, expire_time):
        raise SpuException.NotImplInterface(self.__class__, 'expire')

    def ttl(self, key):
        """
        return -2 if key is not
        return -1 if key is not expire
        return expire second
        """
        raise SpuException.NotImplInterface(self.__class__, 'ttl')

class SpuSearchKeyDict(dict):
    """
    search key dict
    """

    @classmethod
    def get_key_patterm(cls, key_rule):
        key_rule = key_rule.replace('*', '.*')
        if key_rule.startswith('.*') and key_rule.endswith('.*'):
            # prefix and suffix
            rule = key_rule
        if key_rule.startswith('.*'):
            # prefix star
            rule = r'%s$' % key_rule
        elif key_rule.endswith('*'):
            # suffix star
            rule = r'^%s' % key_rule
        else:
            # text
            rule = r'^%s$' % key_rule
        _logging.debug('get_key_patterm gen rule: %s', rule)
        return re.compile(rule)

    def __init__(self, *args, **kwargs):
        """
        init dict
        """
        super(SpuSearchKeyDict, self).__init__(*args, **kwargs)

    def search_key(self, key_rule):
        """
        search key, key support re
        """
        if key_rule == '*':
            return self.keys()

        keys = []
        key_patterm = SpuSearchKeyDict.get_key_patterm(key_rule)
        for key in self.keys():
            if key_patterm.match(key):
                keys.append(key)
        return keys

# Cache ImplInterface
class SpuCacheProcessCache(SpuCacheBase):
    """Sputnik Process Cache Base On Process Memory"""
    def __init__(self, cachecnf):
        SpuCacheBase.__init__(self, cachecnf)
        self._cache = SpuSearchKeyDict()

    def connection(self):
        pass

    def close(self):
        self._cache = SpuSearchKeyDict()

    def set_value(self, key, value, expire=0):
        self._cache[self._key(key)] = value

    @get_stat
    def get_value(self, key):
        return self._cache.get(self._key(key), None)

    def remove(self, key):
        key = self._key(key)
        if self._cache.get(key, None):
            self._cache[key] = None
            del self._cache[key]

    def remove_all(self):
        del self._cache
        self._cache = SpuSearchKeyDict()

    def keys(self, key_rule):
        return self._cache.search_key(key_rule)

    def cache_size(self):
        return len(self._cache)

    def get_all(self):
        return self._cache

SpuCreateCache.register_cache('process', SpuCacheProcessCache, policy='default')


_timer_max = lambda a, b: cmp(b, a)
_timer_min = lambda a, b: cmp(a, b)
# Cache ImplInterface
class SpuCacheProcessLRUCache(SpuCacheBase):
    """Sputnik Process Cache Base On Process Memory, LRU Policy"""

    class _cache_item(object):
        location_history = 1
        location_cache = 2

        def __init__(self, original_key, key, value, count=0, expire=0):
            self.original_key = original_key
            self.__in_list = False
            # double linke point
            self.pre = None
            self.next = None
            # timer point
            self.timer_item = None
            # attr
            self.key = key
            self.value = value
            self.count = count
            self.expire = expire
            # lru-k attr
            self.location = 1 # 1 history 2 cache

        def __str__(self):
            return '<CacheItem key:%s value:%s count:%s expire:%s>' % (
                self.key, self.value, self.count, self.expire)

        def set_in_list(self):
            self.__in_list = True

        def set_out_list(self):
            self.__in_list = False

        def in_list(self):
            return self.__in_list

        def add_count(self):
            self.count += 1

        def is_expire(self):
            if self.expire and self.expire <= time.time():
                return True
            return False

    class _lru_list(object):
        def __init__(self):
            self._head = None
            self._tail = None
            self._iter = None
            self._len = 0
            self._lock = threading.RLock()

        def lru_list_lock(func):
            def _func(self, *args, **kwargs):
                with self._lock:
                    return func(self, *args, **kwargs)
            return _func

        @lru_list_lock
        def __len__(self):
            return self._len

        def __iter__(self):
            self._iter = self._head
            return self

        def next(self):
            if self._iter == None:
                raise StopIteration
            item = self._iter
            self._iter = item.next
            return item

        def _check_new_item(self, new_item):
            assert not new_item.next and not new_item.pre, \
                   'Duplicate Item %s' % new_item

        # common

        @lru_list_lock
        def length(self):
            """
            real length
            """

            l = 0
            item = self._head
            while item:
                l += 1
                item = item.next
            return l

        @lru_list_lock
        def empty(self):
            if not self._head:
                assert not self._tail, 'Not empty tail:%s' % self._tail
                return True
            assert self._tail, 'Not empty head:%s' % self._tail
            return False

        @lru_list_lock
        def head(self):
            return self._head

        @lru_list_lock
        def tail(self):
            return self._tail

        # double linke

        @lru_list_lock
        def insert_head(self, new_item):
            self._check_new_item(new_item)
            new_item.set_in_list()
            self._len += 1
            if not self._head:
                assert not self._tail, 'Tail error %s' % self._tail
                self._head = new_item
                self._tail = new_item
                return
            new_item.pre = None
            new_item.next = self._head
            self._head.pre = new_item
            self._head = new_item

        @lru_list_lock
        def insert_tail(self, new_item):
            self._check_new_item(new_item)
            new_item.set_in_list()
            self._len += 1
            if not self._tail:
                assert not self._head, 'Head error %s' % self._head
                self._head = new_item
                self._tail = new_item
                return
            new_item.next = None
            new_item.pre = self._tail
            self._tail.next = new_item
            self._tail = new_item

        @lru_list_lock
        def insert_next(self, item, new_item):
            self._check_new_item(new_item)
            new_item.set_in_list()
            # head
            if not item:
                self.insert_head(new_item)
                return

            self._len += 1
            # tail
            if not item.next:
                item.next = new_item
                new_item.pre = item
                new_item.next = None
                self._tail = new_item
                return

            next = item.next
            item.next = new_item;
            new_item.next = next
            new_item.pre = item
            next.pre = new_item

        def insert_pre(self, item, new_item):
            if item:
                item = item.pre
            self.insert_next(item, new_item)

        @lru_list_lock
        def remove(self, item):
            if not item.in_list():
                return

            self._len -= 1
            if not item.pre and not item.next:
                self._head = None
                self._tail = None
            else:
                # head
                if not item.pre:
                    self._head = item.next
                    self._head.pre = None
                    item.next = None
                # tail
                elif not item.next:
                    self._tail = item.pre
                    self._tail.next = None
                    item.pre = None
                else:
                    item.pre.next = item.next
                    item.next.pre = item.pre
            item.pre = None
            item.next = None
            item.set_out_list()

        # stack

        def push(self, item):
            self.insert_head(item)

        def pop(self):
            item = self.head()
            self.remove(item)
            return item

        def tail_pop(self):
            item = self.tail()
            self.remove(item)
            return item

        # list

        @lru_list_lock
        def __getitem__(self, index):
            if index > self._len - 1:
                raise IndexError(index)

            item = self._head
            for i in range(index):
                item = item.next
            return item

        def append(self, item):
            self.insert_tail(item)

        # fifo

        def put(self, item):
            self.append(item)

        def get(self):
            item = self._head
            self.remove(item)
            return item

        ###

        @lru_list_lock
        def list(self):
            return [item for item in self]

        @lru_list_lock
        def reverse_list(self):
            l = []
            item = self._tail
            while item:
                l.append(item)
                item = item.pre
            return l

    class _timer_item(object):
        def __init__(self, item, max_heap):
            self.item = item
            item.timer_item = self
            self.expire = item.expire
            self._cmp_func = _timer_max if max_heap else \
                             _timer_min

        def __cmp__(self, item):
            return self._cmp_func(self.expire, item.expire)

    class _Timer(object):
        def __init__(self, check_expire_interval=1,
                     max_time=False):
            """
            check_expire_interval: second
            """
            self._timer_heap = []
            self._max_time = max_time
            self._last_time = 0
            self._interval = check_expire_interval
            self._lock = threading.RLock()

        def timer_lock(func):
            def _func(self, *args, **kwargs):
                with self._lock:
                    return func(self, *args, **kwargs)
            return _func


        def __len__(self):
            return len(self._timer_heap)

        def _push(self, item):
            heapq.heappush(self._timer_heap, item)

        def _pop(self):
            return heapq.heappop(self._timer_heap)

        def _top(self):
            if len(self._timer_heap):
                return self._timer_heap[0]
            return None

        @timer_lock
        def add_item(self, item, expire):
            """
            expire: second
            """

            item.expire = time.time() + expire
            timer_item = SpuCacheProcessLRUCache._timer_item(item, self._max_time)
            self._push(timer_item)

        @timer_lock
        def get_expire_items(self, max_expire_remove):
            expire_item_list = []
            t = time.time()
            if t - self._last_time < self._interval:
                return expire_item_list

            top = self._top()
            if not top or top.expire > t:
                self._last_time = time.time()
                return expire_item_list

            max_expire_remove = max_expire_remove if max_expire_remove else \
                                len(self._timer_heap)

            for i in range(max_expire_remove):
                timer_item = self._pop()
                if not timer_item.item.is_expire():
                    self._push(timer_item)
                    break
                item = timer_item.item
                item.timer_item = None
                expire_item_list.append(item)

            self._last_time = time.time()
            return expire_item_list

        @timer_lock
        def remove(self, item):
            if not item.timer_item:
                _logging.warn('Item not timer_item item: %s', item)
                return
            self._timer_heap.remove(item.timer_item)
            item.timer_item = None

    def __init__(self, cachecnf):
        """
        k: lru-k
        history_size: history list size
        cache_size: cache list size
        """
        SpuCacheBase.__init__(self, cachecnf, 'md5')
        self._history_size = cachecnf.get('history_size', 10000*5)
        self._cache_size = cachecnf.get('cache_size', 100000*5)
        self._k = cachecnf.get('k', 2)
        self._max_expire_remove = cachecnf.get('max_expire_remove', 0)
        self._expire = cachecnf.get('expire', 0)

        self._init_cache()

        self._debug_time = SpuDebugTime()

    def _init_cache(self):
        # cache memory struct
        self._cache = SpuSearchKeyDict()
        self._lru_history = self._lru_list()
        self._lru_cache = self._lru_list()
        # heap top is min time
        self._timer = self._Timer(max_time=False)

    def _remove_item(self, item):
        # remove history or lru cache
        if item.location == item.location_history:
            self._lru_history.remove(item)
        elif item.location == item.location_cache:
            self._lru_cache.remove(item)

        # remove timer
        if item.timer_item:
            self._timer.remove(item)

        # remove cache
        if item.key in self._cache:
            del self._cache[item.key]

        del item

    def _expire_process(self):
        with self._debug_time:
            expire_items = self._timer.get_expire_items(self._max_expire_remove)
            for item in expire_items:
                self._remove_item(item)
        _logging.debug('expire process time: %s', self._debug_time.use_time)

    def _lru_cache_add(self, item):
        if len(self._lru_cache) >= self._cache_size:
            # remove lru cache tail item
            self._remove_item(self._lru_cache.tail())
        # item into lru cache head
        self._lru_cache.push(item)
        item.location = item.location_cache

    def _lru_cache_adjust(self, item):
        # move to lru cache head
        self._lru_cache.remove(item)
        self._lru_cache.push(item)

    def _history_add(self, item):
        if len(self._lru_history) >= self._history_size:
            # remove lru history tail item
            self._remove_item(self._lru_history.tail())
        # item into lru history head
        self._lru_history.push(item)
        item.location = item.location_history

    def _history_adjust(self, item):
        self._lru_history.remove(item)
        # move to cache
        if item.count >= self._k:
            self._lru_cache_add(item)
        # move to history head
        else:
            self._lru_history.push(item)

    def connection(self):
        pass

    def close(self):
        del self._cache
        self._cache = SpuSearchKeyDict()
        del self._lru_history
        self._lru_history = None
        del self._lru_cache
        self._lru_cache = None
        del self._timer
        self._timer = None

    def set_value(self, key, value, expire=0):
        """
        expire: second
        """
        self._expire_process()
        original_key = key
        expire = expire if expire else self._expire
        key = self._key(key)
        item = self._cache.get(key, None)
        if item:
            self._remove_item(item)
        item = self._cache_item(original_key, key, value, expire=expire)
        self._history_add(item)

        if expire:
            self._timer.add_item(item, expire)

        self._cache[key] = item

    def _get_item(self, key):
        self._expire_process()

        key = self._key(key)
        item = self._cache.get(key, None)
        if not item:
            return None

        # real expire
        if item.is_expire():
            self._remove_item(item)
            return None

        return item

    @get_stat
    def get_value(self, key):
        item = self._get_item(key)
        if not item:
            return None

        item.add_count()
        if item.location == item.location_history:
            self._history_adjust(item)
        elif item.location == item.location_cache:
            self._lru_cache_adjust(item)
        else:
            assert 0, 'Unknow location item: %s' % item
        return item.value

    def remove(self, key):
        self._expire_process()

        key = self._key(key)
        item = self._cache.get(key, None)
        if not item:
            return

        self._remove_item(item)

    def remove_by_keyrule(self, keyrule):
        keys = self.original_keys(keyrule)
        for key in keys:
            self.remove(key)

    def remove_all(self):
        del self._cache
        del self._lru_history
        del self._lru_cache
        del self._timer
        self._init_cache()

    def keys(self, key_rule):
        self._expire_process()

        return self._cache.search_key(key_rule)

    def original_keys(self, key_rule):
        """
        search original key, key support re
        """
        self._expire_process()

        keys = []
        if key_rule == '*':
            for value in self._cache.values():
                keys.append(value.original_key)
            return keys

        key_patterm = SpuSearchKeyDict.get_key_patterm(key_rule)
        for value in self._cache.values():
            original_key = value.original_key
            if key_patterm.match(original_key):
                keys.append(original_key)
        return keys

    def cache_size(self):
        self._expire_process()

        return len(self._cache)

    def get_all(self):
        self._expire_process()

        cache = {}
        for key, value in self._cache.items():
            cache[key] = {value.original_key : value.value}
        return cache

    def expire(self, key, expire_time):
        expire_time = int(expire_time)
        item = self._get_item(key)
        if not item:
            return False

        # has expire, remove timer
        if item.timer_item:
            self._timer.remove(item)

        # add new expire time
        self._timer.add_item(item, expire_time)
        return True

    def ttl(self, key):
        item = self._get_item(key)
        if not item:
            return -2
        if not item.timer_item:
            return -1
        return int(item.expire - time.time())

SpuCreateCache.register_cache('process', SpuCacheProcessLRUCache, policy='lru')

# Cache ImplInterface
class SpuCacheRemoteCache(SpuCacheBase):
    """Remote Cache Base On Redis"""
    def __init__(self, cachecnf):
        SpuCacheBase.__init__(self, cachecnf)
        self._redis = None

    def connection(self):
        pool = redis.ConnectionPool(
            host=self._cachecnf['host'],
            port=self._cachecnf['port'],
            db=self._cachecnf['db'])
        self._redis = redis.Redis(connection_pool=pool)

    def close(self):
        pass

    def set_value(self, key, value, expire=0):
        "expire is second"
        if not expire:
            expire = self._cachecnf.get('expire', 0)
        self._redis.set(key, value)
        if expire:
            self._redis.expire(key, expire)

    @get_stat
    def get_value(self, key):
        s = self._redis.get(key)
        if not s:
            return None
        return s

    def remove(self, key):
        self._redis.delete(key)

    def remove_all(self):
        return self._redis.flushdb()

    def keys(self, key_rule):
        return self._redis.keys(key_rule)

    def cache_size(self):
        return self._redis.dbsize()

    def get_all(self):
        cache = {}
        for key in self.keys('*'):
            cache[key] = self.get_value(key)
        return cache

    def expire(self, key, expire_time):
        return self._redis.expire(key, expire_time)

    def ttl(self, key):
        return self._redis.ttl(key)

SpuCreateCache.register_cache('remote', SpuCacheRemoteCache, policy='default')


##
# external base cache class
##

class SpuXCache:
    def __init__(self, doctype, cachecnf, debug = False):
        cache = SpuCreateCache(cachecnf)
        self._cache = cache.create()
        self._doctype = '_' + doctype + '_'
        self._expire = cachecnf.get('expire', 600) # 10 minute
        self._debug = debug

    def _key(self, key_cond):
        return self._doctype + str(key_cond)
