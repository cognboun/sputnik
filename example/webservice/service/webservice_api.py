#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 2013 2014 msx.com
# by error.d@gmail.com
# 2014-08-26
#

import sys
sys.path.append('../')

from config import *
from error import Error
from module.module import FoodAndPlace

from sputnik.SpuPythonObject import SDict
from sputnik.SpuLogging import *
from sputnik.SpuContext import SpuContext
from sputnik.SpuRequest import *
from sputnik.SpuDBObject import *
from sputnik.SpuUOM import *

from sputnik.SpuCacheManager import (fcache_add, fcache_remove_by_keys,
                                     fcache_reset_cache, fcache_no_cache,
                                     fcache_remove,
                                     nocache_call, resetcache_call)

def test_decorator(func):
    print 'test_decorator'

    @UOM_WRAPS(func)
    def w(self, *args, **kwargs):
        print 'call decorator'
        print 'tornado : %s' % self.tornado
        self._write('hello~~')
        print args, kwargs
        return func(self, *args, **kwargs)
    return w

class _cache_test(object):
    def __init__(self):
        self._data = {}

    def set_data(self, _id, data):
        print "set_data id:%s data:%s" % (_id, data)
        self._data[_id] = data

    def _key(self, _id):
        return '_' + str(_id) + '_'

    @fcache_add(primary_key=1)
    def get_data(self, _id, b, new):
        print "get_data id:%s" % _id
        return self._data[_id]

    @fcache_add(primary_key=[1,2])
    def get_data2(self, _id, b, new):
        print "get_data id:%s" % _id
        return self._data[_id]

    @fcache_add(expire=10)
    def get_data_expire(self, _id):
        print "get_data_expire id:%s" % _id
        return self._data[_id]

    @fcache_reset_cache
    def update_data(self, _id, data):
        print "update_data id:%s data:%s" % (_id, data)
        self._data[_id] = data

    @fcache_no_cache
    def nocache_data(self, _id, data):
        print "update_data id:%s data:%s" % (_id, data)
        self._data[_id] = data

    def del_data(self, _id):
        print "del_data id:%s" % _id
        del self._data[_id]
        fcache_remove_by_keys(self.get_data, self._key(_id))

    @fcache_remove(get_data, primary_key=1)
    def fcache_del_data(self, _id):
        print "del_data id:%s" % _id
        del self._data[_id]

    @fcache_remove(get_data2, primary_key=[1,2])
    def fcache_del_data2(self, _id, b):
        print "del_data id:%s" % _id
        del self._data[_id]


cache_test_obj = _cache_test()

class api(SpuRequestHandler):
    _logging = SpuLogging(None, 'api')
    
    def __init__(self):
        pass
    
    def test(self):
        fap_list = FoodAndPlace.find_list()
        self._logging.debug('test')
        self._logging.error('zhizhimama')
        return self._response(PyobjectList(Error.success, fap_list))

    def set_data(self, _id, data):
        cache_test_obj.set_data(_id, data)
        return self._response(PyobjectList(Error.success, "ok"))

    def get_data(self, _id, b):
        data = cache_test_obj.get_data(_id, b, new=234)
        print 'a'*100, data
        return self._response(PyobjectList(Error.success, data))

    def get_data2(self, _id, b):
        data = cache_test_obj.get_data2(_id, b, new=234)
        print 'a'*100, data
        return self._response(PyobjectList(Error.success, data))

    def get_data_expire(self, _id):
        data = cache_test_obj.get_data_expire(_id)
        print 'a'*100, data
        return self._response(PyobjectList(Error.success, data))

    def update_data(self, _id, data):
        cache_test_obj.update_data(_id, data)
        return self._response(PyobjectList(Error.success, "ok"))

    def nocache_data(self, _id, data):
        cache_test_obj.nocache_data(_id, data)
        return self._response(PyobjectList(Error.success, "ok"))

    def del_data(self, _id):
        cache_test_obj.del_data(_id)
        return self._response(PyobjectList(Error.success, "ok"))

    def fcache_del_data(self, _id):
        cache_test_obj.fcache_del_data(_id)
        return self._response(PyobjectList(Error.success, "ok"))

    def fcache_del_data2(self, _id, b):
        cache_test_obj.fcache_del_data2(_id, b)
        return self._response(PyobjectList(Error.success, "ok"))

    def error(self):
        0/0

    def test_kwargs(self,
                    a={'atype' : int},
                    b={'atype' : str, 'adef': 'asf'},
                    **kwargs):
        return self._response(Pyobject(Error.success, kwargs))

    @POST
    def test_post(self,
                  a={'atype' : int},
                  b={'atype' : str},
                  **kwargs):
        return self._response(Pyobject(Error.success, kwargs))

    def request_cache(self,
                      a={'atype': int}):
        fap_list = FoodAndPlace.find_list()
        fap_list = FoodAndPlace.find_list()
        fap_list = FoodAndPlace.find_list()
        return self._response(PyobjectList(Error.success, fap_list))

    def request_no_use_cache(self,
                      a={'atype': int}):
        fap_list = FoodAndPlace.objectlist(use_cache=False)
        fap_list.find('id > 0')
        fap_list.find('id > 0')
        fap_list.find('id > 0')
        return self._response(PyobjectList(Error.success, fap_list))

    def request_nocache_call(self,
                             a={'atype': int}):
        fap_list = FoodAndPlace.find_list()
        fap_list = nocache_call(FoodAndPlace.find_list)
        fap_list = FoodAndPlace.find_list()
        return self._response(PyobjectList(Error.success, fap_list))


    def request_resetcache_call(self,
                                a={'atype': int}):
        fap_list = FoodAndPlace.objectlist()
        fap_list.find('id > 0')
        fap_list.find('id > 0')
        fap_list.find('id > 0')        
        resetcache_call(fap_list.find, 'id > 0')
        fap_list.find('id > 0')
        fap_list.find('id > 0')
        fap_list.find('id > 0')
        return self._response(PyobjectList(Error.success, fap_list))
    
    @test_decorator
    def api_decorator(self,
                      a={'atype' : int},
                      b={'atype' : str, 'adef': 'asf'}):
        """
        AAAAAAAAAAAAAAAAAAAAA
        """
        
        return self._response(Pyobject(Error.success, {'a': a, 'b':b}))


    @test_decorator
    @POST
    def api_decorator_post(self,
                      a={'atype' : int},
                      b={'atype' : str, 'adef': 'asf'}):
        """
        AAAAAAAAAAAAAAAAAAAAA
        """
        
        return self._response(Pyobject(Error.success, {'a': a, 'b':b}))

    def test_list_arg(self,
                      l={'atype' : list}
                      ):
        return self._response(Pyobject(Error.success, l))
