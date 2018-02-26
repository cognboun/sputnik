#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright: error.d
# Date  : 2014-10-15
# Create by: error.d<error.d@gmail.com>
#

import sys
sys.path.insert(0, '../')

import time
import sputnik.SpuUtil as util
from sputnik_config import *
from sputnik.SpuCacheManager import SpuCacheManager, fcache_add, \
     fcache_remove_by_keys, fcache_remove_by_func, fcache_reset_cache, \
     fcache_remove

cache_config = {
    'process' : {
    'enable' : True,
    'type' : 'process',
    'policy': 'lru',
    'expire': 60*5,
            },
    'local' : {
    'enable' : False,
    'type' : 'remote',
    'db': 6,
    'host': '127.0.0.1',
    'port': 6380
            },
    'global' : {
    'enable' : False,
    'type' : 'remote',
    'db': 6,
    'host': '10.132.62.119',
    'port': 6380
            },
        }

def setUp():
    SpuCacheManager.setting(cache_config, True)

def tearDown():
    pass

class _cache_test(object):
    def __init__(self):
        self._data = {}

    def set_data(self, _id, data):
        print "set_data id:%s data:%s" % (_id, data)
        self._data[_id] = data

    def _key(self, func, _id, *args, **kwargs):
        return '_' + str(_id) + '_'

    @fcache_add(_key)
    def get_data(self, _id):
        print "get_data id:%s" % _id
        return self._data[_id]

    @fcache_add(_key, expire=3)
    def get_data_expire(self, _id):
        print "get_data_expire id:%s" % _id
        return self._data[_id]

    @fcache_remove(key_func=_key)
    def update_data(self, _id, data):
        print "update_data id:%s data:%s" % (_id, data)
        self._data[_id] = data

    def del_data(self, _id):
        print "del_data id:%s" % _id
        del self._data[_id]
        fcache_remove_by_keys(self._key(None, _id))

def TestFunctionCache():
    cache_test_obj = _cache_test()

    try:
        cache_test_obj.get_data(1)
    except KeyError:
        pass
    else:
        assert 0, 'get_data faield'
    
    cache_test_obj.set_data(1, 1111)
    assert cache_test_obj.get_data(1) == 1111, 'get_data failed'
    cache_test_obj.set_data(1, 2222)
    assert cache_test_obj.get_data(1) == 1111, 'get_data failed'
    cache_test_obj.update_data(1, 2222)
    assert cache_test_obj.get_data_expire(1) == 2222, 'get_data failed'
    cache_test_obj.set_data(1, 3333)
    assert cache_test_obj.get_data(1) == 2222, 'get_data failed'
    time.sleep(3)
    assert cache_test_obj.get_data_expire(1) == 3333, 'get_data failed'
    cache_test_obj.del_data(1)
    try:
        cache_test_obj.get_data(1)
    except KeyError:
        pass
    else:
        assert 0, 'get_data faield'
    
    cache_test_obj.update_data(1, 88888)
    assert cache_test_obj.get_data(1) == 88888, 'get_data failed'
