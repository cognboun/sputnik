#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-12-17
#
# Sputnik Count Cache
#   缓存count类的sql
# ToDoList:
# 

import redis
import SpuUtil as util
import SpuException
from SpuCache import *

class SpuCountCache(SpuXCache):
    def __init__(self, doctype, cachecnf, debug = False):
        SpuXCache.__init__(self, doctype, cachecnf, debug)

    def _key(self, key):
        return SpuXCache._key(self, util.md5(key))
    
    def get_count(self, count_sql):
        count = self._cache.get_value(self._key(count_sql))
        if count:
            return int(count)
        return count

    def set_count(self, count_sql, count):
        self._cache.set_value(self._key(count_sql), count, self._expire)
