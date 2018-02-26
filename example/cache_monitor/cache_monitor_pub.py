import time
import logging
from sputnik import sputnik_init

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


sputnik_init(debug_logging_config)

logging.getLogger().setLevel(logging.DEBUG)

from SpuCacheMonitor import SpuCacheMonitor

cache_monitor = SpuCacheMonitor('tcp://*:2222', None)
cache_monitor.remove_process_cache_event('bbb')

