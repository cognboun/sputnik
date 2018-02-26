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

from SpuCacheMonitor import SpuCacheMMConsumer, SpuCacheMonitor

cm = SpuCacheMonitor('tcp://*:2222', SpuCacheMMConsumer('tcp://*:5555'))
cm.start_monitor_thread()

i = 0
while True:
    logging.debug('main %s', i)
    i += 1
    time.sleep(1)
