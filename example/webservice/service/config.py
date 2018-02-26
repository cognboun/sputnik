#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 2013 2014 msx.com
# by error.d@gmail.com
# 2014-08-26
#

"""

"""
import sys
import os
import logging
from tornado.options import define, options, parse_command_line, enable_pretty_logging

configfile = sys.argv[-1]
dirname, basename = os.path.split(configfile)
module_name = basename.split('.')[0]
sys.path.append(dirname)
cm = __import__(module_name)

define("server_port", default=None, help="run on the given server port", type=int)
define("app_port", default=None, help="run on the given application port", type=int)
define("debug", default=None, help="debug", type=bool)
parse_command_line()

DEBUG = options.debug or cm.debug
app_port = options.app_port

# logging config
debug_logging_config = {
    'log_slow' : True,
    'log_slow_time' : 500,
    'flowpath_db_detail' : True,
    'flowpath_cache_detail' : True,
    'log_function' : {
        'all' : False,
        'flowpath' : {
            'all' : False,
            'flowpath' : False,
            'logic' : False,
            'service' : False,
            'db' : True,
            'cache' : True
            },
        'perf' : {
            'all' : False,
            'perf' : False,
            'func' : False,
            'service' : False,
            'db' : True,
            'cache' : True
            }
        }    
    }
if DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
    logging_config = debug_logging_config
else:
    logging_config = cm.logging_config

warning_config = {
    'model_field_define_check' : True
    }

run_mode = cm.run_mode

from sputnik import sputnik_init

print logging_config

spusys_config = {
    'enable': True,
    'spumaster_server_addr': '127.0.0.1:12345',
    'app_port': app_port,
    'http_thread': False,
    'network_interface': 'eth0'
    }

sputnik_init(logging_config,
             debug=DEBUG,
             assert_config=warning_config,
             spusys_config=spusys_config)

import sputnik.SpuConfig as SpuConfig
from sputnik.SpuFieldFilter import SpuFieldFilter
from sputnik.SpuDB import SpuDB_Tornado, SpuDBCreateDB
from sputnik.SpuContext import SpuContext
from sputnik.SpuDBObject import *
from sputnik.SpuUOM import SpuUOM
from sputnik.SpuFS import *
from sputnik.SpuDebug import *
from sputnik.SpuFactory import *
from sputnik.SpuCacheManager import SpuCacheManager
from sputnik.SpuRequest import SpuRequestHandler
from sputnik.SpuLogging import start_sputnik_logging

from sputnik.SpuCallTracker import CallTrackerEngine

# global config
SpuConfig.SpuDebug = DEBUG
SpuFieldFilter.debug = DEBUG

# database config
dbcnf = {
    'dbtype' : SpuDB_Tornado,
    'host' : cm.db_host,
    'port' : cm.db_port,
    'database' : cm.db_database,
    'user' : cm.db_user,
    'passwd' : cm.db_password,
    'debug' : DEBUG
    }
