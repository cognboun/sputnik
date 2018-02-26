#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-16
#
# Sputnik Error
#
# 

class SpuErrorCodeGen:
    base = 0
    default_section = 1000

    @classmethod
    def get_base_code(cls, section):
        if not section:
            section = cls.default_section
        base = cls.base
        cls.base += section
        return base

    def __init__(self, section = None):
        self.base_code = SpuErrorCodeGen.get_base_code(section)
    
    def code(self):
        c = self.base_code
        self.base_code += 1
        return c

__code_gen = None

def code():
    global __code_gen
    if not __code_gen:
        # 0 -- 100
        __code_gen = SpuErrorCodeGen(100)
    return __code_gen.code()

class SpuError:
    unknow_error = code()
    success = code()
    unknow_db_failed = code()
