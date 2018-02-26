#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-9
#
# Sputnik Format  Manager:
#   input python object, output json or jsonp or xml format
#
# ToDoList:
# 

import re
from SpuJson import *
import SpuUtil as util

class SpuDataFormat:
    def __init__(self):
        pass

    @classmethod
    def json(cls, pyobject, format=False, format_argument=None):
        python_object = pyobject.python_object()
        return json_dump(python_object, format = format, python_object = python_object)

    @classmethod
    def jsonp(cls, pyobject, format_argument=None):
        def filter(text):
            text = re.sub('\\\\', '\\\\\\\\', text)
            text = re.sub('\"', '\\"', text)
            return text
        json = cls.json(pyobject)
        if format_argument is None:
            return "var jsonp = \"" + filter(json) + "\""
        else:
            format_argument = re.sub(r'<.+?>', '', format_argument)
            return "%s(" % format_argument + json + ")"

    @classmethod
    def xml(cls, pyobject):
        return "xmlllllll"

    @classmethod
    def format(cls, pyobject, format_type='json', format_argument=None):
        """ return json if default or type error"""
        if not format_type or not hasattr(cls, format_type):
            format_type = 'json'
        method = getattr(cls, format_type)
        return method(pyobject, format_argument=format_argument)
