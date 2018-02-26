#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 2013 2014 msx.com
# by error.d@gmail.com
# 2014-08-20
#

import sys
sys.path.insert(0, '../')

from sputnik.SpuCallTracker import CallTrackerEngine
import call_track_test
import call_track_test2

cte = CallTrackerEngine(import_module=call_track_test)
cte.calltrack_module(call_track_test)
cte.calltrack_module(call_track_test2)
call_track_test.test_main(6)

