#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2014-9-26
#
# 

import sys
sys.path.insert(0, '../')

import random
from sputnik_config import *
from sputnik.SpuCache import SpuCacheProcessLRUCache

def gen_lru(size):
    lru = SpuCacheProcessLRUCache._lru_list()
    item_c = SpuCacheProcessLRUCache._cache_item
    for i in range(size):
        lru.append(item_c(i, i))
    return lru

def gen_list(size):
    item_list = []
    for i in range(size):
        item_list.append(i)
    return item_list

def random_num(r, size):
    r_list = []
    for i in range(size):
        while True:
            n = random.randint(0, r-1)
            if n not in r_list:
                break
        r_list.append(n)
    return r_list

def random_num_to_lru(random_list, lru_list):
    l = []
    for i in random_list:
        l.append(lru_list[i])
    return l

def list_remove(random_remove, test_list):
    for i in random_remove:
        test_list.remove(i)
    return len(test_list)

size = 100000
random_size = 5000
random_list = random_num(size, random_size)
print random_list
num_test_list = gen_list(size)
test_lru_list = gen_lru(size)
test_list = random_num_to_lru(random_list, test_lru_list)
print '-'*10

def test_cache():
    print list_remove(random_list, num_test_list)
    print num_test_list
    print list_remove(test_list, test_lru_list)
    n = [item.value for item in test_lru_list.list()]
    print n
    print n == num_test_list

def test_2():
    list_remove(random_list, num_test_list)

def test_3():
    list_remove(test_list, test_lru_list)
    
#test_cache()
