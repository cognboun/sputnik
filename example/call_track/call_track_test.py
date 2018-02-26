#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 2013 2014 msx.com
# by error.d@gmail.com
# 2014-09-18
#

import sys
from call_track_test2 import *

def test1(a, b, c, d):
    return a + b + c * d

def test2(a):
    a = test3(a)
    return a/3

def test3(a):
    a = test4(a)
    return a + a

def test4(a):
    return a - 5

class Test(object):
    def __init__(self):
        pass

    def test(self, a, b, c, d):
        return a+1, b+2, c+3, d+4

def cc(a, b, c=23, d="asd"):
    pass

def cc2(a, b, c=23, d="asd", *args):
    pass

def cc3(a, b, c=23, d="asd", *args, **kwargs):
    print a, b, c, d, args, kwargs

def cc4(a, b, c, d, *args, **kwargs):
    pass

def test_main(a):
    t = Test()
    (a, b, c, d) = t.test(a, a+1, a+2, a*3)
    a = test1(a, b, c, d)
    print test2(a)
    cc(1234, 325)
    cc2(323, 42345, 555, d="ffff")
    cc3('asdf', 'fs', 234, 432, f='fff', e='eee')
    cc3('asdf', 'fs', 234, 432, 82, 63, "dddsdf", 82, f='fff', e='eee')
    cc3('asdf', 'fs', 234, 432, 82, 63, "dddsdf", 82, f='算法')
    cc3('asdf', 'fs', 234, 432, 82, 63, "dddsdf", 82, f=u'算法方法')
    c2_test(a, b, c, d)
    print c2_test

def calltrack_main(a, b, c):
    test_main(int(a))

