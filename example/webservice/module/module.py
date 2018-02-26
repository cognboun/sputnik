#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 2013 2014 msx.com
# by error.d@gmail.com
# 2014-08-26
#

from datetime import datetime
from sputnik.SpuDBObject import SpuDBObject, Field
from sputnik.SpuDateTime import SpuDateTime

class FoodAndPlace(SpuDBObject):
    _table_ = 'sputnik.food_and_place'
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
