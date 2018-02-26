#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-12-9
#

from SpuLogging import *
from SpuDebug import *

_logging = SpuLogging(module_name = 'SpuFieldFilter')
_debugtime = SpuDebugTime()

class SpuFieldFilter:
    debug = False
    def __init__(self):
        self._field_filter = {}

    def add_field_filter(self, filters, delete=0):
        """filter rule like: ('field', filter_function_object)
        filter_function like def filter(field, value) and return (new_field, new_value)
        delete 1 删除原来的key
        """
        for filter in filters:
            field = filter[0]
            filter_function = filter[1]
            if not self._field_filter.get(field, None):
                self._field_filter[field] = []
            self._field_filter[field].append((filter_function, delete))

    def remove_field_filter(self, field, idx = 0):
        """[TODO] if idx is 0, remove all field filter"""
        pass

    def process_all_field_filter(self, fields):
        if not self._field_filter:
            return

        _debugtime.start()
        _logging.set_class_func('SpuFieldFilter', 'process_all_field_filter')
        _logging.flowpath('Field Table : %s' % fields)
        _logging.flowpath('Find Field : %s' % self._field_filter.keys())
        for field in self._field_filter.keys():
            value = fields.get(field, None)
            if value == None:
                continue
            _logging.flowpath('Process : %s' % field)
            filter_chain = self._field_filter[field]
            if not filter_chain:
                continue
            
            old_field = field
            delete = 0
            for filter, delete in filter_chain:
                (field, value) = filter(field, value)

            if delete == 1:
                del fields[old_field]
            fields[field] = value
        t = _debugtime.end()
        _logging.perf('', t)

    def process_field_filter(self, field, value):
        if not self._field_filter:
            return (field, value)

        filter_chain = self._field_filter.get(field, None)
        if not filter_chain:
            return (field, value)
        
        for filter in filter_chain:
            (field, value) = filter(field, value)
        return (field, value)
