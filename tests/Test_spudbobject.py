#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright: error.d
# Date  : 2014-08-21
# Create by: error.d<error.d@gmail.com>
#

from sputnik_config import *
from sputnik.SpuDB import *
from sputnik.SpuDBObject import *
from sputnik.SpuDateTime import SpuDateTime


class FoodAndPlace(SpuDBObject):
    _table_ = 'food_and_place'
    def __init__(self, spudb, spucache, debug):
        SpuDBObject.__init__(self, FoodAndPlace._table_, spudb, spucache, debug = debug)
        self.id = Field(int, 0, 8, auto_inc = True)
        self.place_id = Field(int, 0, 8)
        self.food_id = Field(int, 0, 8)
        self.picture_count = Field(int, 0, 4) # 1000
        self.comment_total = Field(int, 0, 5) # 10000
        self.publish_time = Field(datetime, SpuDateTime.current_time())
        self.best_picture_id = Field(int, 0, 8)
        self.want_it_total = Field(int, 0, 6)
        self.nom_it_total = Field(int, 0, 6)


dbcnf = {
    'dbtype' : SpuDB_Tornado,
#    'host' : '115.236.23.187:6033',
#    'port' : 6033,
    'host' : '127.0.0.1:3306',
    'port' : 3306,
#    'database' : 'msx_db_dev',
    'database' : 'sputnik',
    'user' : 'root',
#    'passwd' : 'shuotao1234!@#$shuotao',
    'passwd' : '',
    'debug' : True
    }

dbc = None

def setUp():
    global dbc
    db = SpuDBCreateDB(dbcnf)
    dbc = db.create()
    dbc.set_charset('utf8mb4')
    dbc.connection()

def tearDown():
    dbc.close()

def TestFind():
    fap = FoodAndPlace(dbc, None, True)
    fap_t = FoodAndPlace.table()
    fap.find(fap_t.id == 10)
    objlist = SpuDBObjectList(FoodAndPlace, dbc, None, True)
    objlist.find((fap_t.id > 1) & (fap_t.id < 10))
    assert len(objlist) == 0, "objlist len %s" % len(objlist)
