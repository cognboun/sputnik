#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-13
#
# Sputnik Context
#
# ToDoList:
# 

from SpuDB import SpuDBManager
from SpuDBObject import *
from SpuMongoDBObject import *

class SpuContext:
    """
    
    """
    g_spudb = None
    g_mongodb = None
    
    @classmethod
    def init_context(cls, spudb, mongodb):
        cls.g_spudb = spudb
        cls.g_mongodb = mongodb

    @classmethod
    def get_g_spudb(cls):
        return cls.g_spudb

    @classmethod
    def get_g_mongodb(cls):
        return cls.g_mongodb

    def __init__(self, spudb, spucache, mongodb = None):
        self._spudb = spudb
        self._spucache = spucache
        self._mongodb = mongodb
        SpuDBManager.add_spudb(self._spudb)
        SpuCurMongoDB.set_mongodb(self._mongodb)

    def spudb(self):
        return self._spudb

    def spucache(self):
        return self._spucache

    def mongodb(self):
        return self._mongodb

    def createModule(self, cls, empty = False, debug = False):
        """
        废弃，使用SpuFactory中得create_object
        """
        
        c = cls(self.spudb(), self.spucache(), debug = debug)
        if hasattr(c, 'map_db_field'):
            c.map_db_field()
        if empty and hasattr(c, 'clear_all_field'):
            c.clear_all_field()
        return c

    def createModuleList(self, table, debug = False):
        """
        废弃，使用SpuFactory中得create_listobject
        """
        
        if hasattr(table, '_table_'):
            table = table._table_
        l = SpuDBObjectList(table, self.spudb(), self.spucache(), debug = debug)
        return l
