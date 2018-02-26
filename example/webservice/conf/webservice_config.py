#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 2013 2014 msx.com
# by error.d@gmail.com
# 2014-08-26
#

"""

"""

run_mode = 'dev'

debug = False
app_port = 0

db_port = 3306
db_host = '127.0.0.1'
db_database = 'sputnik'
db_user = 'root'
db_password = ''

logging_config = {
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

