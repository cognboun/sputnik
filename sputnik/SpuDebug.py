#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-11-18
#
# Sputnik Debug
#
# ToDoList:
# 

import time
import math
from sputnik import is_debug
from SpuLogging import *
from SpuUtil import *

def performance_function(func):
    def f(self, **kwargs):
        performance_time.start()
        r = func(self, **kwargs)
        time = performance_time.end()
        _logging = SpuLogging()
        _logging.perf_func(func, "%s" % time)
        return r
    func.__call__ = f
    func.replace_method = True
    return func

def performance_function_1(func):
    def f(self, arg):
        performance_time.start()
        r = func(self, arg)
        time = performance_time.end()
        _logging = SpuLogging()
        _logging.perf_func(func, "%s" % time)
        return r
    return f

class SpuDebugBlock(object):
    """
    SpuDebugBlock
    """
    
    def __init__(self, exception_func=None):
        """
        """
        self._exception_func = exception_func

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_tb and is_debug():
            return False
        elif exc_tb and self._exception_func:
            self._exception_func(exc_value)
        return True

class SpuDebugTime:
    def __init__(self, classinfo = ''):
        self.s_time = None
        self.e_time = None
        self.use_time = 0
        self._logging = SpuLogging(module_name='SpuDebug',
                                   class_name=classinfo, tag_name='DebugTime')

    # use with
    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_value, exc_tb):
        # use xx.use_time get result
        self.use_time = self.end()
        if exc_tb:
            return False
        return True

    def __str__(self):
        return self.time()

    def set_classinfo(self, classinfo):
        self._logging.set_class(classinfo)

    def set_function(self, function):
        self._logging.set_function(function)

    def start(self):
        self.s_time = time.time()

    def end(self):
        self.e_time = time.time()
        return self.time()

    def point(self, msg = ''):
        if msg:
            self._logging.perf(msg, self.end())
        else:
            self._logging.perf(self.end())
        self.start()

    def time(self, s = False):
        r = self.e_time - self.s_time
        r *= 100000
        r = int(r)
        r = float(r) / 100000
        if s:
            return str(r) + 's'
        else:
            return str(r * 1000) + 'ms'

GDebugTime = SpuDebugTime()

performance_time = SpuDebugTime('performance')
def SetPerformanceTime(debug):
    performance_time.set_debug(debug)
