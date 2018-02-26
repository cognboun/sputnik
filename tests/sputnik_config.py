#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright: error.d
# Date  : 2014-09-26
# Create by: error.d<error.d@gmail.com>
#

import sys
sys.path.insert(0, '../')


import logging

debug_logging_config = {
    'log_slow' : False,
    'log_slow_time' : 500,
    'log_function' : {
        'all' : True,
        'flowpath' : {
            'all' : True,
            'flowpath' : True,
            'logic' : True,
            'service' : True,
            'db' : True,
            'cache' : True
            },
        'perf' : {
            'all' : True,
            'perf' : True,
            'func' : True,
            'service' : True,
            'db' : True,
            'cache' : True
            }
        }
    }    

from sputnik import sputnik_init
logging.getLogger().setLevel(logging.DEBUG)
sputnik_init(debug_logging_config)
