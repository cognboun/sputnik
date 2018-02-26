#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-9
#
# Sputnik DataBase
#  对数据库进行了封装，屏蔽了应用对具体数据库的依赖，当前只支持mysql
# ToDoList:
# 

import re
import time
import json
import copy
import datetime
import hashlib
import MySQLdb
import pymongo
import bson
import threading
import tornado.database
import SpuException
import SpuUtil as util
from SpuLogging import *
from SpuDebug import *

default_server = 'default_server'

_logging = SpuLogging(module_name = 'SpuDB', app_log=False)

class UnknowDB(SpuException.SpuException):
    def __init__(self, dbname):
        self._dbname = dbname
    
    def __str__(self):
        return 'Unknow Database (%s)' % self._dbname

class UnknowDBException(SpuException.SpuException):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return msg    

class DBDuplicateEntry(SpuException.SpuException):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return self._msg

class DBCnfFailed(SpuException.SpuException):
    def __init__(self, dbcnf):
        self._dbcnf = dbcnf

    def __str__(self):
        str = ''
        if not self._dbcnf:
            str = 'Not dbcnf'
            return str
        if not self._dbcnf.get('dbtype', None):
            str += 'Not dbtype'
        if not self._dbcnf.get('host', None):
            str += 'Not host'
        if not self._dbcnf.get('port', None):
            str += ', Not port'
        if not self._dbcnf.get('database', None):
            str += ', Not database'
        if not self._dbcnf.get('user', None):
            str += ', Not user'
        if not self._dbcnf.get('passwd', None):
            str += ', Not passwd'
        return str

class RollbackExcept(SpuException.SpuException):
    def __init__(self):
        pass

    def __str__(self):
        return "Database Rollback"

class SpuDBManager:
    db_server = {}
    
    @classmethod
    def add_spudb(cls, spudb, server=default_server):
        _logging.set_class_func('SpuDBManager', 'add_spudb')
        
        assert not cls.db_server.get(server, None), "Duplicate DB Server %s" % server
        cls.db_server[server] = spudb
        
        _logging.flowpath_db(spudb)

    @classmethod
    def check_db(cls, server=default_server):
        spudb = cls.db_server.get(server,None)
        assert spudb, "no server:%s please call SpuDBManager.add_spudb" % server

    @classmethod
    def get_spudb(cls, server=default_server):
        cls.check_db()
        spudb = cls.db_server[server]
        return spudb
    
    @classmethod
    def remove_spudb(cls, server=default_server):
        _logging.set_class_func('SpuDBManager', 'remove_spudb')

        spudb = cls.db_server.pop(server, None)

class Transaction(object):
    def __init__(self,
                 server=default_server,
                 only_rollback_exception=False,
                 raise_exception=True):
        """
        only_rollback_exception : only raise RollbackExcept rollback database, default is True, all Exception rollback database
        raise_exception: to pass raise exception, but RollbackExcept not raise. default is True
        """
        
        self._server = server
        self._dbc = SpuDBManager.get_spudb(self._server)
        self._only_rollback_exception = only_rollback_exception
        self._raise_exception = raise_exception

    def __enter__(self):
        self._dbc.start_transaction()
        _logging.spu_debug('start transaction')

    def __exit__(self, exc_type, exc_value, exc_tb):
        if not exc_tb:
            self._dbc.commit()
            _logging.spu_debug('transaction success, commit')
            return True

        _logging.spu_debug('transaction failed')
        if not self._only_rollback_exception or exc_type is RollbackExcept :
            self._dbc.rollback()
            _logging.spu_debug('transaction rollback')

        if self._raise_exception and exc_type is not RollbackExcept:
            return False
        return True

def transaction_process(func):
    def process(*args, **kwargs):
        r = None
        with Transaction():
            r = func(*args, **kwargs)
        return r
    return process

def transaction_process_setting(
    server=default_server,
    only_rollback_exception=False,
    raise_exception=True):

    def wrapper(func):
        def process(*args, **kwargs):
            r = None
            with Transaction(server, only_rollback_exception,
                             raise_exception):
                r = func(*args, **kwargs)
            return r
        return process
    return wrapper

class SpuDB:
    def __init__(self, dbcnf):
        self._dbcnf = dbcnf
        try:
            self._host = self._dbcnf['host']
            self._port = self._dbcnf['port']
            self._database = self._dbcnf['database']
            self._user = self._dbcnf['user']
            self._passwd = self._dbcnf['passwd']
            self._charset = self._dbcnf.get('charset', 'utf8')
            self._debug = self._dbcnf.get('debug', 0)
        except Exception as m:
            raise DBCnfFailed(dbcnf)
        self._debug_time = SpuDebugTime()
        self._logging = SpuLogging(app_log=False)

    def filter_string(self, sql):
        sql = re.sub('%', '%%', sql)
        return sql

    def connection(self):
        raise SpuException.NotImplInterface(self.__class__, 'connect')

    def reconnect(self):
        raise SpuException.NotImplInterface(self.__class__, 'reconnect')

    def close(self):
        raise SpuException.NotImplInterface(self.__class__, 'close')

    def escape(self, v):
        raise SpuException.NotImplInterface(self.__class__, 'escape')

    def query(self, sql):
        raise SpuException.NotImplInterface(self.__class__, 'query')

    def execsql(self, sql):
        raise SpuException.NotImplInterface(self.__class__, 'execsql')

    def db(self):
        raise SpuException.NotImplInterface(self.__class__, 'db')

    def set_charset(self, charset):
        raise SpuException.NotImplInterface(self.__class__, 'set_charset')

    def start_transaction(self):
        raise SpuException.NotImplInterface(self.__class__, 'start_transaction')

    def commit(self):
        raise SpuException.NotImplInterface(self.__class__, 'commit')

    def rollback(self):
        raise SpuException.NotImplInterface(self.__class__, 'rollback')


class SpuDBCreateDB:
    def __init__(self, dbcnf):
        self._dbcnf = dbcnf

    def create(self):
        try:
            cls = self._dbcnf['dbtype']
        except Exception as m:
            raise DBCnfFailed(dbcnf)

        return cls(self._dbcnf)

class SpuDB_Mysql(SpuDB):
    def __init__(self, dbcnf):
        SpuDB.__init__(self, dbcnf)
        self._db = None

class SpuDB_Tornado(SpuDB):
    def __init__(self, dbcnf):
        SpuDB.__init__(self, dbcnf)
        self._logging.set_class('SpuDBTornado')
        self._sql_lock = threading.Lock()        

    def __str__(self):
        s = "<SpuDB_Tornado connection:%s handler:%s " \
            "host:%s port:%s database:%s user:%s>" % (self._db,
                                                      self._db._db,
                                                      self._host, 
                                                      self._port,
                                                      self._database,
                                                      self._user)
        return s

    def connection(self):
        self._logging.set_function('connection')
        self._debug_time.start()
        self._db = tornado.database.Connection(
            host = self._host, 
            database = self._database,
            user = self._user, 
            password = self._passwd)
        t = self._debug_time.end()
        self._logging.flowpath_db(str(self), t)
        # seting names == character_set_connection and
        # character_set_client charsets set
        self.execsql('set names %s' % self._charset)
        # setting time_zone
        time_zone = self.query('select @@global.time_zone, @@session.time_zone;')
        self._logging.info('init mysql time_zone: %s', time_zone)
        self.execsql("set session time_zone = 'SYSTEM';")
        time_zone = self.query('select @@global.time_zone, @@session.time_zone;')
        self._logging.info('updated mysql time_zone: %s', time_zone)

    def reconnect(self):
        _logging.spu_error('Reconnect Database')
        self._logging.set_function('reconnect')
        self._debug_time.start()
        self._db.reconnect()
        t = self._debug_time.end()
        self._logging.flowpath_db(str(self),t)
        self.execsql('set names %s' % self._charset)

    def close(self):
        self._db.close()

    def escape(self, value):
        # fixbug: self._db._db is None
        # look tornado source database.py _ensure_connected method
        if self._db and not self._db._db:
            self.reconnect()

        assert self._db and self._db._db, "escape db is None"
        if type(value) == list:
            for i in range(len(value)):
                if type(value[i]) == unicode:
                    value[i] = util.to_string(value[i])
        elif type(value) == unicode:
            value = util.to_string(value)
        return self._db._db.escape(value)

    def print_error_sql(self, msg, exception):
        SpuLogging.error_dump_frame("[ErrorSql]Sql: (%s) Exception: (%s)" % (msg, exception))

    def query(self, sql):
        self._logging.set_function('query')
        self._debug_time.start()
        try:
            with self._sql_lock:
                r = self._db.query(self.filter_string(sql))
        except Exception as m:
            self.print_error_sql(sql, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(sql, t, r)
        return r

    def execsql(self, sql):
        self._logging.set_function('execsql')
        self._debug_time.start()
        try:
            with self._sql_lock:
                r = self._db.execute(self.filter_string(sql))
        except MySQLdb.IntegrityError as m:
            self.print_error_sql(sql, m)
            if m[0] == 1062:
                raise DBDuplicateEntry(m)
            else:
                raise UnknowDBException(m)
        except Exception as m:
            self.print_error_sql(sql, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(sql, t)
        return r

    def db(self):
        return self._db

    def set_charset(self, charset):
        self._charset = charset

    def start_transaction(self):
        self.execsql("start transaction;")

    def commit(self):
        self.execsql("commit;")

    def rollback(self):
        self.execsql("rollback;")

class SpuMongodb(SpuDB):
    @classmethod
    def objectid(cls, id):
        if isinstance(id, bson.objectid.ObjectId):
            return id
        return bson.objectid.ObjectId(id)

    def __init__(self, dbcnf):
        SpuDB.__init__(self, dbcnf)
        self._logging.set_class('SpuMongodb')
        self._collection = None

    def _connect_mongodb(self):
        self._connection = pymongo.Connection(self._host,
                                              self._port)
        self._db = self._connection[self._database]

    def __str__(self):
        return "<SpuMongodb collection:%s>" % self._collection

    def clone(self, collection):
        db = SpuMongodb(self._dbcnf)
        db._collection = collection
        db._connection = self._connection
        db._db = self._db
        return db
        
    def connection(self):
        self._logging.set_function('connection')
        self._debug_time.start()
        self._connect_mongodb()
        t = self._debug_time.end()
        self._logging.flowpath_db(str(self), t)

    def reconnect(self):
        _logging.spu_error('Reconnect Database')
        self._logging.set_function('reconnect')
        self._debug_time.start()
        self._connection.disconnect()
        self._connect_mongodb()
        t = self._debug_time.end()
        self._logging.flowpath_db(str(self),t)

    def close(self):
        self._connection.disconnect()
        self._connection = None
        self._db = None

    def print_error_sql(self, msg, exception):
        SpuLogging.error_dump_frame("[ErrorSql]Sql: (%s) Exception: (%s)" % (msg, exception))

    def db(self):
        return self._db

    def set_collection(self, name):
        self._collection = name

    def collection_name(self, name):
        if not name:
            name = self._collection
        return name
    
    def collection(self, name):
        name = self.collection_name(name)
        assert name, "Collection Not Define"
        return self._db[name]

    def collection_count(self, name = None):
        coll = self.collection(name)
        return coll.count()

    def find(self, *args, **kwargs):
        self._logging.set_tag(self._collection)
        self._logging.set_function('find')
        self._debug_time.start()
        try:
            collection = self.collection(None)
            r = collection.find(*args, **kwargs)
        except Exception as m:
            self.print_error_sql(args, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(args, t)
        return r

    def find_one(self, spec_or_id=None, *args, **kwargs):
        self._logging.set_tag(self._collection)
        self._logging.set_function('find_one')
        self._debug_time.start()
        try:
            collection = self.collection(None)
            r = collection.find_one(spec_or_id, *args, **kwargs)
        except Exception as m:
            self.print_error_sql(spec_or_id, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(spec_or_id, t)
        return r

    def find_one_by_id(self, id, *args, **kwargs):
        self._logging.set_tag(self._collection)
        self._logging.set_function('find_one_by_id')
        self._debug_time.start()
        try:
            spec_or_id = {'_id': self.objectid(id)}
            collection = self.collection(None)
            r = collection.find_one(spec_or_id, *args, **kwargs)
        except Exception as m:
            self.print_error_sql(spec_or_id, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(spec_or_id, t)
        return r

    def delete(self, spec_or_id, safe=False, **kwargs):
        self._logging.set_tag(self._collection)
        self._logging.set_function('delete')
        self._debug_time.start()
        try:
            collection = self.collection(None)
            r = collection.remove(spec_or_id, safe, **kwargs)
        except Exception as m:
            self.print_error_sql(spec_or_id, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(spec_or_id, t)
        return r

    def insert(self, doc_or_docs):
        self._logging.set_tag(self._collection)
        self._logging.set_function('insert')
        self._debug_time.start()
        try:
            collection = self.collection(None)
            r = collection.insert(doc_or_docs)
        except Exception as m:
            self.print_error_sql(doc_or_docs, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(doc_or_docs, t)
        return r

    def update(self, spec, document, upsert=False, manipulate=False, safe=False, multi=False, **kwargs):
        self._logging.set_tag(self._collection)
        self._logging.set_function('update')
        self._debug_time.start()
        try:
            collection = self.collection(None)
            sql = {'spec' : spec,
                   'document' : document}
            r = collection.update(spec, document, upsert, manipulate, safe, multi, **kwargs)
        except Exception as m:
            self.print_error_sql(sql, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(sql, t)
        return r

    def update_by_id(self, id, document, upsert=False, manipulate=False, safe=False, multi=False, **kwargs):
        self._logging.set_tag(self._collection)
        self._logging.set_function('update_by_id')
        self._debug_time.start()
        try:
            spec = {'_id': self.objectid(id)}
            collection = self.collection(None)
            sql = {'spec' : spec,
                   'document' : document}
            r = collection.update(spec, document, upsert, manipulate, safe, multi, **kwargs)
        except Exception as m:
            self.print_error_sql(sql, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(sql, t)
        return r

    def set_by_id(self, id, name, value, upsert=False, manipulate=False, safe=False, multi=False, **kwargs):
        """
        update a field
        """
        self._logging.set_tag(self._collection)
        self._logging.set_function('set_by_id')
        self._debug_time.start()
        try:
            spec = {'_id': self.objectid(id)}
            document = {'$set': {name: value}}
            sql = {'spec' : spec,
                   'document' : document}
            collection = self.collection(None)
            r = collection.update(spec, document, upsert, manipulate, safe, multi, **kwargs)
        except Exception as m:
            self.print_error_sql(sql, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(sql, t)
        return r

    def inc_by_id(self, id, name, value, upsert=False, manipulate=False, safe=False, multi=False, **kwargs):
        self._logging.set_tag(self._collection)
        self._logging.set_function('inc_by_id')
        self._debug_time.start()
        try:
            spec = {'_id': self.objectid(id)}
            collection = self.collection(None)
            document = {'$inc': {name: value}}
            sql = {'spec' : spec,
                   'document' : document}
            r = collection.update(spec, document, upsert, manipulate, safe, multi, **kwargs)
        except Exception as m:
            self.print_error_sql(sql, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(sql, t)
        return r

    def push_to_list_by_id(self, id, name, value,
                           upsert=False, manipulate=False, safe=False, multi=False, **kwargs):
        self._logging.set_tag(self._collection)
        self._logging.set_function('push_to_list_by_id')
        self._debug_time.start()
        try:
            spec = {'_id': self.objectid(id)}
            collection = self.collection(None)
            document = {'$push': {name: value}}
            sql = {'spec' : spec,
                   'document' : document}
            r = collection.update(spec, document, upsert, manipulate, safe, multi, **kwargs)
        except Exception as m:
            self.print_error_sql(sql, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(sql, t)
        return r

    def pull_to_list_by_id(self, id, name, value,
                           upsert=False, manipulate=False, safe=False, multi=False, **kwargs):
        """
        remove elements on list
        """
        self._logging.set_tag(self._collection)
        self._logging.set_function('pull_to_list_by_id')
        self._debug_time.start()
        try:
            spec = {'_id': self.objectid(id)}
            collection = self.collection(None)
            document = {'$pull': {name: value}}
            sql = {'spec' : spec,
                   'document' : document}
            r = collection.update(spec, document, upsert, manipulate, safe, multi, **kwargs)
        except Exception as m:
            self.print_error_sql(sql, m)
            raise m
        t = self._debug_time.end()
        self._logging.flowpath_db(sql, t)
        return r

    def geo_near(self, near, maxDistance, distanceMultiplier=100000, stats=False, coll=None, num=10, query=None):
        """
        maxDistance: 0.00001 = 1.11 m, detail at doc[2]
        doclist:
        [1] http://www.mongodb.org/display/DOCS/Geospatial+Indexing#GeospatialIndexing-geoNearCommand
        [2] http://en.wikipedia.org/wiki/Decimal_degrees
        """
        self._logging.set_tag(self._collection)
        self._logging.set_function('geo_near')
        self._debug_time.start()
        sql = ''
        try:
            coll = self.collection_name(coll)
            k = {'near' : near,
                 'maxDistance' : 0.00001 * maxDistance,
                 'distanceMultiplier' : distanceMultiplier,
                 'num': num}
            if query:
                k['query'] = query
            sql = copy.copy(k)
            sql['geoNear'] = coll
            r = self._db.command('geoNear', coll, **k)
        except Exception as m:
            self.print_error_sql(sql, m)
            raise m            
        t = self._debug_time.end()
        self._logging.flowpath_db(sql, t)
        if not stats:
            temp = []
            for item in r['results']:
                item_temp = item['obj']
                item_temp['dis'] = item['dis']
                temp.append(item_temp)
            r = temp
        return r        

if __name__ == '__main__':
    dbcnf = {
        'dbtype' : SpuDB_Tornado,
        'host' : 'localhost',
        'port' : 3306,
        'database' : 'sputnik',
        'user' : 'root',
        'passwd' : '',
        'charset' : 'utf8'
        }
    
    s = SpuDBCreateDB(dbcnf)
    d = s.create()
    d.connection()
    s = d.execsql("show databases")
    print s
