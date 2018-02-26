#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-11-2
#
# Sputnik Base
#
# ToDoList:
# 

class SpuBase:
    def __init__(self,
                 spudb = None,
                 spucache = None,
                 debug = None,
                 base = None):
        assert base or spudb, 'SpuBase Not Init'
        if base:
            spudb = base._spudb
            spucache = base._spucache
            debug = base._debug
        self._spudb = spudb
        self._spucache = spucache
        self._debug = debug
