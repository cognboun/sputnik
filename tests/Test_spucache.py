#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright: error.d
# Date  : 2014-09-26
# Create by: error.d<error.d@gmail.com>
#

import sys
sys.path.insert(0, '../')

import time
import sputnik.SpuUtil as util
from sputnik_config import *
from sputnik.SpuCache import SpuCacheProcessLRUCache

def setUp():
    pass

def tearDown():
    pass

def TestLRUCache():
    lru = SpuCacheProcessLRUCache._lru_list()
    item_c = SpuCacheProcessLRUCache._cache_item
    item1 = item_c(1, 1, 1)
    assert len(lru) == 0, 'lenght failed'
    lru.insert_next(None, item1)
    assert lru.head().key == 1, 'head faield %s' % lru.head()
    assert lru.tail().key == 1, 'tail faield %s' % lru.tail()
    item2 = item_c(2, 2, 2)
    lru.insert_next(item1, item2)
    assert len(lru) == 2, 'lenght failed'    
    assert lru.head().key == 1, 'head faield %s' % lru.head()
    assert lru.tail().key == 2, 'tail faield %s' % lru.tail()    
    item3 = item_c(3, 3, 3)
    lru.insert_next(item2, item3)
    assert lru.head().key == 1, 'head faield %s' % lru.head()
    assert lru.tail().key == 3, 'tail faield %s' % lru.tail()    
    item4 = item_c(4, 4, 4)
    lru.insert_pre(item3, item4)
    assert lru.head().key == 1, 'head faield %s' % lru.head()
    assert lru.tail().key == 3, 'tail faield %s' % lru.tail()    
    item5 = item_c(5, 5, 5)
    lru.insert_pre(item1, item5)
    assert len(lru) == 5, 'lenght failed'
    assert lru.head().key == 5, 'head faield %s' % lru.head()
    assert lru.tail().key == 3, 'tail faield %s' % lru.tail()    
    item6 = item_c(6, 6, 6)
    lru.insert_pre(None, item6)
    assert lru.head().key == 6, 'head faield %s' % lru.head()
    assert lru.tail().key == 3, 'tail faield %s' % lru.tail()
    assert len(lru) == 6, 'lenght failed'

    # 6->5->1->2->4->3

    assert [item.key for item in lru] == [6, 5, 1, 2, 4, 3], 'to list failed'
    assert lru.pop().key == 6, 'cache insert_next or insert_pre failed'
    assert len(lru) == 5, 'lenght failed'
    assert lru.pop().key == 5, 'cache insert_next or insert_pre failed'
    assert lru.pop().key == 1, 'cache insert_next or insert_pre failed'
    assert len(lru) == 3, 'lenght failed'    
    assert lru.pop().key == 2, 'cache insert_next or insert_pre failed'
    assert lru.pop().key == 4, 'cache insert_next or insert_pre failed'
    assert not lru.empty(), 'empyt faield'
    assert lru.pop().key == 3, 'cache insert_next or insert_pre failed'
    assert lru.empty(), 'empyt faield'
    assert len(lru) == 0, 'lenght failed'

    
    lru.push(item1)
    lru.push(item3)
    lru.push(item2)
    lru.pop()
    lru.push(item4)
    lru.pop()
    lru.pop()
    lru.push(item6)
    lru.push(item4)
    lru.pop()
    lru.append(item2)
    lru.push(item5)
    assert len(lru) == 4, 'lenght failed'
    assert [item.key for item in lru] == [5, 6, 1, 2], 'to list failed %s'
    assert lru.list() == [item5, item6, item1, item2], 'list failed'

    assert lru[0] == item5, 'list index error'
    assert lru[1] == item6, 'list index error'
    assert lru[3] == item2, 'list index error'

    try:
        l = lru[4]
        check_index = False
    except IndexError:
        check_index = True
    assert check_index, 'list index error'

    try:
        lru.push(item3)
        lru.push(item3)
        check_new_item = False
    except AssertionError:
        check_new_item = True
    assert check_new_item, 'check new item faield'

    assert lru.list() == [item3, item5, item6, item1, item2], 'list failed'
    assert len(lru) == 5, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'

    lru.remove(item6)
    assert lru.list() == [item3, item5, item1, item2], 'list failed'
    assert len(lru) == 4, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'
    
    lru.remove(item3)
    assert lru.list() == [item5, item1, item2], 'list failed'
    assert len(lru) == 3, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'

    lru.remove(item2)
    assert lru.list() == [item5, item1], 'list failed'
    assert len(lru) == 2, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'

    lru.push(item4)
    lru.pop()
    lru.append(item2)
    lru.insert_next(item1, item4)
    lru.push(item6)
    item7 = item_c(7, 7, 7)
    lru.insert_pre(item4, item7)
    lru.remove(item1)
    assert lru.list() == [item6, item5, item7, item4, item2], \
           'list failed %s' % [item.key for item in lru]
    assert len(lru) == 5, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'    

    lru.remove(item7)
    lru.remove(item4)
    assert lru.list() == [item6, item5, item2], \
           'list failed %s' % [item.key for item in lru]
    assert len(lru) == 3, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'
    
    lru.remove(item6)
    lru.remove(item5)
    lru.remove(item2)

    assert lru.list() == [], 'list failed'
    assert len(lru) == 0, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'

    lru.put(item1)
    lru.put(item2)
    lru.put(item3)
    lru.put(item4)

    assert lru.list() == [item1, item2, item3, item4], 'list failed'
    assert len(lru) == 4, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'

    assert lru.get() == item1, "get failed"
    assert lru.get() == item2, "get failed"
    assert lru.get() == item3, "get failed"
    assert lru.get() == item4, "get failed"    

    assert lru.list() == [], 'list failed'
    assert len(lru) == 0, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'

    # bug: remove duplicate item
    lru.push(item1)
    lru.push(item2)
    lru.push(item3)
    lru.push(item4)

    lru.remove(item3)
    assert len(lru) == 3, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'
    
    lru.remove(item3)
    assert len(lru) == 3, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'

    assert lru.tail_pop() == item1, 'tail_pop faield'
    assert lru.tail_pop() == item2, 'tail_pop faield'
    assert lru.tail_pop() == item4, 'tail_pop faield'    
    assert len(lru) == 0, 'lenght failed'
    assert len(lru) == lru.length(), 'lenght failed'

def TestTimer():
    timer = SpuCacheProcessLRUCache._timer()
    item_c = SpuCacheProcessLRUCache._cache_item
    item1 = item_c(1, 1, 1)
    item2 = item_c(2, 2, 2)
    item3 = item_c(3, 3, 3)
    item4 = item_c(4, 4, 4)   

    timer.add_item(item1, 5)
    timer.add_item(item2, 5)
    timer.add_item(item3, 10)
    timer.add_item(item4, 15)

    l = timer.get_expire_items(0)
    assert not l, 'real get_expire_items failed'

    time.sleep(6)
    l = timer.get_expire_items(0)
    assert l == [item1, item2], 'sleep 5 get_expire_items failed: %s' % l

    time.sleep(1)
    l = timer.get_expire_items(0)
    assert not l, 'real get_expire_items failed'
    
    time.sleep(4)
    l = timer.get_expire_items(0)
    assert l == [item3], 'sleep 10 get_expire_items failed'

    time.sleep(5)
    l = timer.get_expire_items(0)
    assert l == [item4], 'sleep 15 get_expire_items failed'

    assert len(timer) == 0, 'timer no empty'

def TestSpuCacheProcessLRUCache():
    conf = {
        'history_size': 5,
        'cache_size' : 10,
        'k': 2
        }

    cache = SpuCacheProcessLRUCache(conf)
    cache.set_value('abcd', 2132)
    assert cache.get_value('abcd') == 2132, 'get_value failed'
    cache.set_value('1', 111, 2)
    cache.set_value('2', 222, 4)
    cache.set_value('3', 333, 6)
    cache.set_value('4', 444, 8)    
    assert cache.get_value('1') == 111, 'get_value failed'
    time.sleep(1)
    assert cache.get_value('1') == 111, 'get_value failed'
    time.sleep(1)
    assert cache.get_value('abcd') == 2132, 'get_value failed'
    assert cache.get_value('1') == None, 'get_value failed'
    assert cache.get_value('2') == 222, 'get_value failed'
    assert cache.get_value('3') == 333, 'get_value failed'
    assert cache.get_value('4') == 444, 'get_value failed'    
    time.sleep(2)
    assert cache.get_value('abcd') == 2132, 'get_value failed'
    assert cache.get_value('1') == None, 'get_value failed'
    assert cache.get_value('2') == None, 'get_value failed'
    assert cache.get_value('3') == 333, 'get_value failed'
    assert cache.get_value('4') == 444, 'get_value failed'        
    time.sleep(2)
    assert cache.get_value('abcd') == 2132, 'get_value failed'
    assert cache.get_value('1') == None, 'get_value failed'
    assert cache.get_value('2') == None, 'get_value failed'
    assert cache.get_value('3') == None, 'get_value failed'
    assert cache.get_value('4') == 444, 'get_value failed'    
    time.sleep(2)
    assert cache.get_value('abcd') == 2132, 'get_value failed'
    assert cache.get_value('1') == None, 'get_value failed'
    assert cache.get_value('2') == None, 'get_value failed'
    assert cache.get_value('3') == None, 'get_value failed'    
    assert cache.get_value('4') == None, 'get_value failed'

    assert len(cache._lru_history) == 0, '_lru_history size failed'
    assert len(cache._lru_cache) == 1, '_lru_cache size failed'

    cache.set_value(1, 1)
    cache.set_value(2, 2)
    cache.set_value(3, 3)
    cache.set_value(4, 4)
    cache.set_value(5, 5)
    cache.set_value(6, 6)
    cache.set_value(7, 7)
    cache.set_value(8, 8)

    assert len(cache._lru_history) == 5, '_lru_history size failed'
    assert len(cache._lru_cache) == 1, '_lru_cache size failed'

    assert cache.get_value(1) == None, 'get_value failed'
    assert cache.get_value(2) == None, 'get_value failed'
    assert cache.get_value(3) == None, 'get_value failed'
    assert cache.get_value(4) == 4, 'get_value failed'
    assert cache.get_value(5) == 5, 'get_value failed'
    assert cache.get_value(6) == 6, 'get_value failed'
    assert cache.get_value(7) == 7, 'get_value failed'
    assert cache.get_value(8) == 8, 'get_value failed'

    assert len(cache._lru_history) == 5, '_lru_history size failed'
    assert len(cache._lru_cache) == 1, '_lru_cache size failed'

    cache.get_value(5)
    cache.get_value(8)
    cache.get_value(7)

    assert len(cache._lru_history) == 2, '_lru_history size failed'
    assert len(cache._lru_cache) == 4, '_lru_cache size failed'

    assert cache._lru_history.length() == 2, 'lru history length failed'
    assert cache._lru_history[0].key == 6, 'lru history key failed'
    assert cache._lru_history[1].key == 4, 'lru history key failed'

    cache.set_value(9, 9)
    cache.set_value(10, 10)
    assert cache._lru_history[0].key == 10, 'lru history key failed'
    assert cache._lru_history[1].key == 9, 'lru history key failed'
    cache.get_value(9)
    assert cache._lru_history[0].key == 9, 'lru history key failed'
    assert cache._lru_history[1].key == 10, 'lru history key failed'    
    assert cache._lru_history.length() == 4, 'lru history length failed'

    assert cache._lru_cache.length() == 4, 'lru cache length failed'
    assert cache._lru_cache[0].key == 7, 'lru cache key failed'
    assert cache._lru_cache[1].key == 8, 'lru cache key failed'
    assert cache._lru_cache[2].key == 5, 'lru cache key failed'
    assert cache._lru_cache[3].key == util.md5('abcd'), 'lru cache key failed'


    cache.get_value(9)
    cache.get_value(10)
    cache.get_value(10)    
    cache.set_value(11, 11)
    cache.set_value(12, 12)
    cache.set_value(13, 13)
    cache.set_value(14, 14)
    cache.set_value(15, 15)    
    cache.get_value(11)
    cache.get_value(11)
    cache.get_value(12)
    cache.get_value(12)        

    assert cache._lru_cache.length() == 8, 'lru cache length failed'
    assert cache._lru_cache[7].key == util.md5('abcd'), 'lru cache key failed'

    cache.get_value(13)
    cache.get_value(13)
    cache.get_value(14)
    cache.get_value(14)        

    assert cache._lru_cache.length() == 10, 'lru cache length failed'
    assert cache._lru_cache[9].key == util.md5('abcd'), 'lru cache key failed'

    cache.get_value(15)
    cache.get_value(15)        

    assert cache.get_value('abcd') == None, 'get value failed'

    # reset
    cache.set_value(113, 123)
    assert cache.get_value(113) == 123, 'reset value failed'
    cache.set_value(113, 124)
    assert cache.get_value(113) == 124, 'reset value failed'
    cache.set_value(113, 125)
    assert cache.get_value(113) == 125, 'reset value failed'

def TestSpuCacheProcessLRUCache_max_expire_remove():
    conf = {
        'history_size': 10,
        'cache_size' : 10,
        'k': 2,
        'max_expire_remove': 10
        }

    cache = SpuCacheProcessLRUCache(conf)
    for i in range(20):
        cache.set_value(i, i, 0.5)
    time.sleep(1)
    expire_list = cache._timer.get_expire_items(10)
    assert len(expire_list) == 10, 'get_expire_items failed'
    for i in range(20):
        assert cache.get_value(i) == None, 'get_value failed'
    expire_list = cache._timer.get_expire_items(0)
    assert len(expire_list) == 0, 'get_expire_items failed'

    ####
    conf = {
        'history_size': 20,
        'cache_size' : 20,
        'k': 2,
        'max_expire_remove': 0
        }

    cache = SpuCacheProcessLRUCache(conf)
    for i in range(20):
        cache.set_value(i, i, 0.5)
    time.sleep(1)
    expire_list = cache._timer.get_expire_items(0)
    assert len(expire_list) == 20, 'get_expire_items failed %s' % len(expire_list)
    for i in range(20):
        assert cache.get_value(i) == None, 'get_value failed'
    expire_list = cache._timer.get_expire_items(0)
    assert len(expire_list) == 0, 'get_expire_items failed'

def TestSpuCacheProcessLRUCache_sql():
    conf = {
        'history_size': 10,
        'cache_size' : 10,
        'k': 2,
        'max_expire_remove': 10
        }

    cache = SpuCacheProcessLRUCache(conf)
    sql = "select tp.property_id, tp.property_value, p.name, p.access_type, p.value_type from spu_property as tp   join (property as p ) on (tp.property_id = p.id) where tp.spu_id = '829'"
    cache.set_value(sql, '111')
    assert cache.get_value(sql) == '111', 'sql cache faield'
