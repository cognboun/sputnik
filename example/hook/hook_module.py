#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 2013 2014 msx.com
# by error.d@gmail.com
# 2014-08-20
#

import sys
sys.path.insert(0, '../')

import logging
from sputnik.Sputnik import set_logging_config
from sputnik.SpuHook import SpuHook as Hook, HookHandler


class handler(HookHandler):
    def call(hook_type, hook_object, *args, **kwargs):
        print 'hook_module .... ', hook_type, hook_object, args, kwargs

class TestMethodHook(object):
    def __init__(self):
        self._ttc = 'tttcccc'

    @Hook.hook(handler)
    def test_method(self, d):
        print '-- test_method_hook_class hehe 00~~', self, self._ttc, d

class TestHook(object):

    def __init__(self):
        self._aa = 'abcd123'

    def test(self):
        print 'test_class', self._aa, TestHook.test
        self.test2('fasdf', '23432xdf')

    def test2(self, a, b, c=10):
        print a, b, c
        self.test3(a, b, 20, 32, c=234, d='asdf')

    def test3(self, ab, cd, *args, **kwargs):
        print ab, cd, args, kwargs
        self._test4()

    def _test4(self):
        print 'ttt  ttttt tt'
        self.__test5()

    def __test5(self):
        print '55555555555 ttttt tt'


@Hook.hook
def test_hook(a, c='default___self'):
    print 'test_function', a, c

def test_hook2(a, c='default___self'):
    print 'test_function2', a, c

class TestHook_handler(object):

    def __init__(self):
        pass

    def test(self):
        print 'test_handler_class'

def test_main():
    test_hook2('asdfsadf', c='asfsdf')
    test_hook2('asdfsadf', c='asfsdf')
    test_hook2('asdfsadf', c='asfsdf')
    test_hook2('asdfsadf', c='asfsdf')

    t = TestHook_handler()
    t.test()

