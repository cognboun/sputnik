#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
@Author niusmallnan

'''

import redis
import SpuUtil
import SpuException
import SpuConfig

class SpuCeleryCache:

    celery_conf = None
    db_connection = None

    @classmethod
    def init_cacheserver(cls, conf):
        cls.celery_conf = conf

    @classmethod
    def connection(cls):
        if not cls.celery_conf:
            celery_cache_config = SpuConfig.SpuCeleryCache_Config
            SpuCeleryCache.init_cacheserver(celery_cache_config['celery_cache_db_config'])

        pool = redis.ConnectionPool(
            host = cls.celery_conf['host'],
            port = cls.celery_conf['port'],
            db = cls.celery_conf['db'])
        cls.db_connection = redis.Redis(connection_pool=pool)

    @classmethod
    def get_connection(cls):
        if not cls.db_connection:
            cls.connection()
        return cls.db_connection

    def __init__(self):
        self._connection = self.get_connection()
        self._type = 'celery'

    def remove(self, user_id):
        link_key = '%s_%s' % (self._type, user_id)
        self._connection.delete(link_key)

    def put(self, user_id, expire=None):
        link_key = '%s_%s' % (self._type, user_id)
        if not expire:
            expire = self.celery_conf.get('expire', 0)
        self._connection.set(link_key, 0)
        if expire:
            self._connection.expire(link_key, expire)

    def contain(self, user_id):
        link_key = '%s_%s' % (self._type, user_id)
        return self._connection.exists(link_key)



