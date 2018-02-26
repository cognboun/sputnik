#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-12-20
#
# Sputnik Cache Object
#   提供了对cache操作的接口
#   根据SpuDataObject提供的操作原语操作cache
#
# ToDoList:
# 

import redis
import SpuUtil
import SpuException
import SpuUtil as util
from SpuJson import *
from SpuPythonObject import *
from SpuDBObject import *
from SpuCache import *

class SpuCacheObject(SpuPythonObject):
    """
    SpuCacheObject class attribute field like _xx,
    SpuPythonObject class attribute(doc field) field like xx,
    """
    def __init__(self, doc):
        SpuPythonObject.__init__(self)
        self.__dict__['_doc'] = doc

    def __str__(self):
        field_dict = self.python_object()
        string = json_string(field_dict, format = True)
        return "<SpuCacheObject: %s>" % util.to_string(string)

    def _get_doc(self):
        return self.__dict__['_doc']

    def _set_field(self, name, value):
        if name[0] == '_':
            self.__dict__[name] = value
        else:
            self.add_field(name, value)

    def _get_field(self, name):
        if name[0] == '_':
            return self.__dict__[name]
        else:
            doc = self._get_doc()
            if self.is_python_object(doc):
                return doc.get_db_field_value(name)
            else:
                return doc.get(name, None)

    def add_field(self, name, value):
        doc = self._get_doc()
        if self.is_python_object(doc):
            doc.add_field(name, value)
        else:
            if hasattr(value, 'python_object'):
                value = value.python_object()
            doc[name] = value

    def get(self, key, default = None):
        doc = self._get_doc()
        return doc.get(key, default)

    def __setattr__(self, name, value):
        return self._set_field(name, value)

    def __setitem__(self, name, value):
        return self._set_field(name, value)

    def __getattr__(self, name):
        return self._get_field(name)

    def __getitem__(self, name):
        return self._get_field(name)

    def _python_object(self):
        doc = self._get_doc()
        self.setup_field_filter(doc)
        if self.is_python_object(doc):
            return doc.python_object()
        self.process_field_filter(doc)
        return doc

class SpuCacheObjectList(SpuPythonObjectList):
    def __init__(self):
        SpuPythonObjectList.__init__(self)
        self._docs = []
        self._pageinfo = None

    def __iter__(self):
        return self._docs.__iter__()

    def __len__(self):
        return len(self._docs)

    def __setitem__(self, name, value):
        self._docs[name] = value

    def __getslice__(self, index1, index2):
        return self._docs[index1:index2]

    def get_pythonobject_list(self):
        return self._docs

    def pageinfo(self, pageinfo):
        self._pageinfo = pageinfo

    def append(self, doc):
        self._docs.append(doc)

    def set_lastone_pageinfo(self, pageinfo):
        self._pageinfo = pageinfo

    def get_lastone_pageinfo(self):
        return self._pageinfo

