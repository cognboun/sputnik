#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2014-9-26
#
# 


import sys
sys.path.insert(0, '../../')

import time
import random
from sputnik_config import *
from sputnik.SpuCache import SpuCacheProcessLRUCache

timer = SpuCacheProcessLRUCache._timer()
item_c = SpuCacheProcessLRUCache._cache_item
item1 = item_c(1, 1)
item2 = item_c(2, 2)
item3 = item_c(3, 3)
item4 = item_c(4, 4)   

timer.add_item(item1, 5)
timer.add_item(item2, 5)
timer.add_item(item3, 10)
timer.add_item(item4, 15)

l = timer.get_expire_items()
print 'real get_expire_items %s' % l

time.sleep(6)
l = timer.get_expire_items()
print 'sleep 5 get_expire_items %s' % l

time.sleep(1)
l = timer.get_expire_items()
print 'real get_expire_items %s' % l

time.sleep(4)
l = timer.get_expire_items()
print 'sleep 10 get_expire_items %s' % l

time.sleep(5)
l = timer.get_expire_items()
print 'sleep 15 get_expire_items %s' % l

print 'timer count %s' % len(timer)
