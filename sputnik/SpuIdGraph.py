#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2012 msx.com
# by benbendy@163.com
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

class SpuIdGraph:
    id_graph_conf = None
    db_connection = None

    @classmethod
    def init_id_graph(cls, conf):
        """
        {
        'enable' : True,
        'host': 'localhost',
        'port': 6379
        }
        """
        cls.id_graph_conf = conf

    @classmethod
    def connection(cls):
        if not cls.id_graph_conf:
            id_graph_config = SpuConfig.SpuIdGraph_Config
            SpuIdGraph.init_id_graph(id_graph_config['id_graph_db_config'])
        pool = redis.ConnectionPool(
            host = cls.id_graph_conf['host'],
            port = cls.id_graph_conf['port'],
            db = cls.id_graph_conf['db'])
      
        cls.db_connection = redis.Redis(connection_pool=pool)

    @classmethod
    def get_connection(cls):
        if not cls.db_connection:
             cls.connection()
        return cls.db_connection
 
    def __init__(self, id_type):
        self._connection = self.get_connection()
        self._id_type = id_type
    
    def clear_link(self, source_node_id, dst_node_type):
        '''
        清除value
        '''
        link_key = "%d_%d_%d" % (self._id_type, source_node_id, dst_node_type)
        self._connection.delete(link_key)

    def create_link(self, source_node_id, dst_node_id, dst_node_type, left=True):
        '''
        '''
        link_key = "%d_%d_%d" % (self._id_type, source_node_id, dst_node_type)
        if left:
            self._connection.lpush(link_key, dst_node_id)
        else:
            self._connection.rpush(link_key, dst_node_id)

        return link_key

    def get_nodelist_by_nodetype(self, source_node_id, dst_node_type, start= None, count= None):
        link_key = "%d_%d_%d" % (self._id_type, source_node_id, dst_node_type)
        if not start:
             start = 0
        if not count:
             count = self._connection.llen(link_key)
        return self._connection.lrange(link_key, start, count-1)

    def del_nodelink_by_nodetype(self, source_node_id, dst_node_id, dst_node_type):
        link_key = "%d_%d_%d" % (self._id_type, source_node_id, dst_node_type)
	self._connection.lrem(link_key, dst_node_id , 1)

    
