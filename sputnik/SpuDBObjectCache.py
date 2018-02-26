#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2012 msx.com
# by error.d@gmail.com
# 2012-4-14
#
# Sputnik DBObject Cache
#
# ToDoList:
#

import redis

class VectorCache:
    def __init__(self):
        pass

class ViewCache:
    def __init__(self):
        pass

class ViewMetadataTable:
    def __init__(self):
        pass

class DataModifyTable:
    def __init__(self):
        pass

class SpuDBObjectCache:
    cache_conf = None
    redis = None

    @classmethod
    def init_dbobject_cache(cls, conf):
        """
        {
        'enable' : True,
        'db': 8,
        'host': 'localhost',
        'port': 6379
        }
        """
        cls.cache_conf = conf
        pool = redis.ConnectionPool(
            host = cls.cache_conf['host'], 
            port = cls.cache_conf['port'], 
            db = cls.cache_conf['db'])
        cls.redis = redis.Redis(connection_pool=pool)

    def __init__(self):
        pass

    def _get_view(self):
        pass

    def _get_view_list(self):
        pass

    def _modify(self, type, dbobject):
        pass

    def set_cache(self, dbobject):
        """
        set dbobject or dbobject list to cache
        """
        pass

    def get_cache(self, dbobject):
        """
        get dbobject from cache
        """
        pass

    def insert_modify(self, dbobject):
        pass

    def update_modify(self, dbobject):
        pass

    def delete_modify(self, dbobject):
        pass
