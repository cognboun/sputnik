#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-12-19
#
# Sputnik Python Object
#
# ToDoList:
# 

import SpuException
from SpuDateTime import SpuDateTime
from SpuLogging import *

class SpuObjectBase(object):
    def __init__(self):
        self._lastone_pageinfo = None
        self._pageinfo = None

    def get_pageinfo(self):
        return self._pageinfo

    def set_lastone_pageinfo(self, pageinfo):
        self._lastone_pageinfo = pageinfo

    def get_lastone_pageinfo(self):
        return self._lastone_pageinfo

    def pageinfo(self, pageinfo):
        self.set_lastone_pageinfo(pageinfo)
        self._pageinfo = pageinfo
        return self
                 
class SpuPythonObjectFilterBase(SpuObjectBase):
    def __init__(self):
        SpuObjectBase.__init__(self)
        self._field_filter = None

    def set_field_filter(self, field_filter):
        self._field_filter = field_filter

    def setup_field_filter(self, obj):
        if self._field_filter and hasattr(obj, 'set_field_filter'):
            obj.set_field_filter(self._field_filter)

    def process_field_filter(self, fields):
        if self._field_filter:
            self._field_filter.process_all_field_filter(fields)

class SpuPythonObject(SpuPythonObjectFilterBase):
    def __init__(self):
        SpuPythonObjectFilterBase.__init__(self)

    def is_python_object(self, obj):
        return hasattr(obj, 'python_object')

    def python_object(self):
        return self._python_object()

    def _python_object(self):
        raise SpuException.NotImplInterface(self.__class__, '_python_object')

class SpuPythonObjectList(SpuPythonObjectFilterBase):
    def __init__(self):
        SpuPythonObjectFilterBase.__init__(self)        

    def python_object(self):
        if hasattr(self, '_python_object'):
            return self._python_object
        flist = []
        objlist = self.get_pythonobject_list()
        for obj in objlist:
            if obj is None:
                SpuLogging.error('[PythonObjectIsNone]')
                continue
            self.setup_field_filter(obj)
            if hasattr(obj, 'python_object'):
                pyobj = obj.python_object()
            else:
                pyobj = obj
            flist.append(pyobj)
        return flist

    def get_pythonobject_list(self):
        raise SpuException.NotImplInterface(self.__class__, 'get_pythonobject_list')

class PyobjectBase:
    field_filter = None

    @classmethod
    def set_field_filter(cls, field_filter):
        cls.field_filter = field_filter

    def __init__(self):
        pass

    def setup_field_filter(self, result):
        if self.field_filter and hasattr(result, 'set_field_filter'):
            result.set_field_filter(self.field_filter)

class Pyobject(PyobjectBase):
    def __init__(self, status, result = {}, append_info = {}):
        PyobjectBase.__init__(self)
        self.setup_field_filter(result)

        if hasattr(result, 'python_object'):
            result = result.python_object()
        if result is None:
            result = {}
        self.pyobject = {'status': status[0],
                         'msg': status[1],
                         'result': result,
                         'append_info': append_info}

    def python_object(self):
        return self.pyobject

class PyobjectList(PyobjectBase):
    def __init__(self, status, result = [], append_info = {}):
        PyobjectBase.__init__(self)
        self.setup_field_filter(result)

        if hasattr(result, 'python_object'):
            pyobj_result = result.python_object()
        else:
            pyobj_result = result
        page_total = 0
        pagenumber = 0
        if type(pyobj_result) == list:
            result_count = len(pyobj_result)
        elif type(pyobj_result) == dict:
            result_count = 1 if len(pyobj_result) else 0
        else:
            result_count = 0
        if hasattr(result, 'get_lastone_pageinfo'):
            pageinfo = result.get_lastone_pageinfo()
            if pageinfo:
                page_total = pageinfo.total_pagenumber if pageinfo.total_pagenumber else 0
                pagenumber = pageinfo.current_pagenumber if pageinfo.current_pagenumber else 0
        if pyobj_result is None:
            pyobj_result = []
        self.pyobject = {'status': status[0],
                         'msg': status[1],
                         'pagenumber': pagenumber,
                         'page_total': page_total,
                         'result_count': result_count,
                         'result': pyobj_result,
                         'append_info': append_info}

    def python_object(self):
        return self.pyobject

class SpuPythonDict(SpuPythonObject, dict):
    def __init__(self, **kwargs):
        SpuPythonObject.__init__(self)
        dict.__init__(self, **kwargs)

    def dict(self, objs):
        for obj in objs:
            self[obj] = objs[obj]

    def _python_object(self):
        _dict = {}
        for key in self.keys():
            value = self[key]
            self.setup_field_filter(value)
            if hasattr(value, 'python_object'):
                pvalue = value.python_object()
            elif isinstance(value, datetime.datetime):
                pvalue = SpuDateTime.datetime2str(value)
            else:
                pvalue = value
            _dict[key] = pvalue
        self.process_field_filter(_dict)
        return _dict

class SpuPythonList(SpuPythonObjectList, list):
    def __init__(self, is_element = False, *args):
        """
        is_element is True *args is a element
        """
        SpuPythonObjectList.__init__(self)
        if not is_element and len(args) == 1 and type(args[0]) == list:
            args = args[0]
        for a in args:
            self.append(a)

    def __str__(self):
        s = []
        for obj in self:
            s.append(obj)
        return "<SpuPythonList: \n%s>" % '\n'.join(map(str,s))

    def list(self, objs):
        for obj in objs:
            self.append(obj)

    def get_pythonobject_list(self):
        return self

class SpuPythonTuple(SpuPythonObjectList, tuple):
    def __init__(self, _list):
        SpuPythonObjectList.__init__(self)
        tuple.__init__(_list)
    
    def python_object(self):
        _list = SpuPythonObjectList.python_object(self)
        return tuple(_list)

    def get_pythonobject_list(self):
        return self

SObject = SpuPythonObject
SObjectList = SpuPythonObjectList
SDict = SpuPythonDict
SList = SpuPythonList
STuple = SpuPythonTuple
