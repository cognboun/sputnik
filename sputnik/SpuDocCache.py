#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-12-17
#
# Sputnik Documents Cache
#   缓存SpuDBObject查询返回的documents(fieldview)
# ToDoList:
# 

import redis
import SpuUtil
import SpuException
from SpuDBObject import *
from SpuCacheObject import *
from SpuCache import *
from SpuLogging import *
from SpuDebug import *

_logging = SpuLogging(module_name = 'SpuDocCache')

class SpuDocCache(SpuXCache):
    def __init__(self, doctype, cachecnf, debug = False):
        SpuXCache.__init__(self, doctype, cachecnf, debug)
        self._debug_time = SpuDebugTime()
        
    def _set_doc(self, key, doc_append_function, dbobject):
        _logging.set_class_func('SpuDocCache', '_set_doc')
        if doc_append_function:
            doc_append_function(dbobject)
        doc = dbobject.python_object()
        self._debug_time.start()
        self._cache.set_value(key, doc, self._expire)
        t = self._debug_time.end()
        _logging.flowpath_cache(key, doc, t)

    def _create_find_object(self, dbobject, listobj = True, sort = False):
        if listobj:
            c = SpuDBObjectList
        else:
            c = SpuDBObject
        object = c(
            dbobject._table,
            dbobject._spudb,
            dbobject._spucache,
            dbobject._debug,
            dbobject._filter_null)
        object.field_view(dbobject.get_field_view())
        object._join = dbobject._join
        if sort:
            object._sort = dbobject._sort
        return object

    def _get_doc_from_db(self, cond_key, dbobject):
        object = self._create_find_object(dbobject, listobj = False)
        field_view = dbobject.get_field_view_object()
        f = field_view.get_cache_condkey_field_origname()
        object.find("%s = %s" % (f, cond_key), new_field = True)
        return object

    def _get_docs_from_db(self, cond_keys, dbobject):
        objectlist = self._create_find_object(dbobject, listobj = True)
        field_view = dbobject.get_field_view_object()
        f = field_view.get_cache_condkey_field_origname()
        objectlist.find(In(f, cond_keys))
        return objectlist

    def _get_condkey_from_dbobject(self, dbobject):
        field_view = dbobject.get_field_view_object()
        if not field_view:
            return None
        return field_view.get_cache_condkey()

    def get_docs(self, cond_list, dbobject, doc_append_function = None, union_query = True):
        """
        cond list(id list) to doc list
        args:
            cond_list : cond list
            dbobject  : SpuDBObject
            doc_append_function : doc_append_function(dbobject)
            union_query : True if cache misses, Through the union inquiry way loading data
        return:
            doc list
        """
        if not cond_list:
            return None

        _logging.set_class_func('SpuDocCache', 'get_docs')
        db_doc_condkeys = []
        db_docs = []
        cacheobject_list = SpuCacheObjectList()

        idx = 0
        condkey_idx = {}
        for cond_key in cond_list:
            key = self._key(cond_key)
            self._debug_time.start()
            doc = self._cache.get_value(key)
            t = self._debug_time.end()
            _logging.flowpath_cache(key, doc, t)
            if not doc:
                if not union_query:
                    doc = self._get_doc_from_db(cond_key, dbobject)
                    assert not (self._debug and not doc), 'Get Doc From Database Failed: %s' % cond_key
                    self._set_doc(key, doc_append_function, doc)
                else:
                    db_doc_condkeys.append(cond_key)
                    condkey_idx[cond_key] = idx
            else:
                # from cache, is string, so eval to python object
                doc = eval(doc)
            cacheobject = None
            if doc:
                cacheobject = SpuCacheObject(doc)
            cacheobject_list.append(cacheobject)
            idx += 1

        if db_doc_condkeys and union_query:
            db_docs = self._get_docs_from_db(db_doc_condkeys, dbobject)
            field_view = dbobject.get_field_view_object()
            assert not (self._debug and len(db_doc_condkeys) != len(db_docs)), ('Get Docs From Database Failed %s %s' % (db_doc_condkeys, db_docs))
            cache_condkey = field_view.get_cache_condkey()
            self.set_docs(db_docs, doc_append_function, cache_condkey)
            for doc in db_docs:
                cacheobject = SpuCacheObject(doc)
                condkey = doc[cache_condkey]
                idx = condkey_idx[str(condkey)]
                cacheobject_list[idx] = cacheobject
        return cacheobject_list

    def set_docs(self, dbobject_list, doc_append_function = None, cond_key = None):
        """
        set doc list to cache
        args:
            dbobject_list: SpuDBObjectList is Doclist
        """
        if not cond_key:
            cond_key = self._get_condkey_from_dbobject(dbobject_list)
        assert cond_key, 'Cond Key Is None'
        for dbobject in dbobject_list:
            key = self._key(dbobject[cond_key])
            self._set_doc(key, doc_append_function, dbobject)

