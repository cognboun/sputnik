#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2012 msx.com
# by error.d@gmail.com
# 2012-6-20
#
# Sputnik Mongodb Object (Mongodb ORM)
# 

import re
import time
import json
import datetime
import hashlib
import SpuException
import SpuUtil as util
from SpuLogging import *
from SpuDB import SpuMongodb
from SpuLogging import *
from SpuDebug import *

_logging = SpuLogging(module_name = 'SpuMongoDBObject')

class SpuCurMongoDB:
    mongodb = None
    
    @classmethod
    def set_mongodb(cls, mongodb):
        _logging.set_class_func('SpuCurMongoDB', 'set_mongodb')
        cls.mongodb = mongodb
        _logging.flowpath_db(cls.mongodb)

    @classmethod
    def check_db(cls):
        assert cls.mongodb, "Mongodb is None"        

    @classmethod
    def get_mongodb(cls):
        cls.check_db()
        return cls.mongodb

class SpuMongoDBObject:
    def __init__(self):
        pass

class SpuMongoDBObjectList:
    def __init__(self):
        pass

if __name__ == '__main__':
    dbcnf = {
        'host' : '115.236.23.187',
        'port' : 27017,
        'database' : 'location',
        'user' : '',
        'passwd' : '',
        }
    
    d = SpuMongodb(dbcnf)
    d.connection()
    s = d.find('places', {'place_id': 1})
    print s.count()
    print s[0]
    print d.collection_count('places')
    s = d.find_one('places', {'place_id': 1})
    print s
    print a > b
