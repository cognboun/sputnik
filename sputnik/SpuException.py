#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-12
#
# Sputnik Exception
#
# ToDoList:
# 

class SpuException(Exception):
    def __init__(self):
        pass

class NotImplInterface(SpuException):
    def __init__(self, class_name, interface_name):
        self._class = class_name
        self._interface = interface_name

    def __str__(self):
        return "\nClass:(%s) Interface:(%s) Not Implementation" % (self._class, self._interface)

class NotDefWebRequestProcesser(SpuException):
    def __init__(self):
        pass

    def __str__(self):
        return "Not Default Web Request Processer"

class UnSupportHookOBject(SpuException):
    def __init__(self, hook_object):
        self._hook_object = hook_object

    def __str__(self):
        return "UnSupport hook object %s" % self._hook_object
