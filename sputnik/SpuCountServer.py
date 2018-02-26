#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2012 msx.com
# by error.d@gmail.com
# 2012-4-24
#
# Sputnik Count Server
#
# ToDoList:
# 

import redis
import SpuUtil
import SpuException
import SpuConfig
from SpuLogging import SpuLogging

class SpuCountServer:
    count_conf = None
    # key: count type -> value: redis connection
    db_connection_table = {}
    db_idx = 0
    _logging = SpuLogging(module_name = 'SpuCountServer',
                          class_name = 'SpuCountServer')

    @classmethod
    def init_countserver(cls, conf):
        """
        {
        'host': 'localhost',
        'port': 6379
        }
        """
        cls.count_conf = conf

    @classmethod
    def connection_countserver(cls, db):
        if not cls.count_conf:
            count_server_config = SpuConfig.SpuCountServer_Config
            SpuCountServer.init_countserver(count_server_config['count_server_db_config'])

        cls._logging.set_function('connection_countserver')
        cls._logging.flowpath_logic('connection',
                                    cls.count_conf['host'],
                                    cls.count_conf['port'],
                                    cls.count_conf['db']
                                    )

        pool = redis.ConnectionPool(
            host = cls.count_conf['host'],
            port = cls.count_conf['port'],
            #host = "127.0.0.1",
            #port = 6380,
            db = cls.count_conf['db'])
        return redis.Redis(connection_pool=pool)

    @classmethod
    def get_connection(cls, type):
        connection = cls.db_connection_table.get(type, None)
        if not connection:
            connection = cls.connection_countserver(cls.db_idx)
            cls.db_connection_table[type] = connection
            cls.db_idx += 1
        return connection
        
    def __init__(self, count_type):
        self._connection = self.get_connection(count_type)
        self._type = count_type

    def get_key(self):
        raise SpuException.NotImplInterface(self.__class__, 'get_key')

    def reset_count(self, count):
        '''
        重新设置count数
        '''
        key = self.get_key()
        self._connection.set(key, count)

    def inc_count(self, amount=1):
        """
        Increments the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as ``amount``
        """
        self._connection.incr(self.get_key(), amount=amount)

    def desc_count(self, amount=1):
        """
        Decrements the value of ``key`` by ``amount``.  If no key exists,
        the value will be initialized as 0 - ``amount``
        """
        self._connection.decr(self.get_key(), amount=amount)        

    def get_count(self):
        self._logging.set_function('get_count')
        key = self.get_key()
        value = self._connection.get(key)
        self._logging.flowpath_cache(key, value)
        if not value:
            return 0 
        return int(value)
