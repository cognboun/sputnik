#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 2013 2014 msx.com
# by error.d@gmail.com
# 2014-08-26
#

"""

"""

import sys
from config import *
from sputnik.SpuError import SpuErrorCodeGen, SpuError
from sputnik.SpuUOM import setdoc

__code_gen = None

def code():
    global __code_gen
    if not __code_gen:
        # 200 -- 1100
        __code_gen = SpuErrorCodeGen(1000)
    return __code_gen.code()

class Error:
    code_dict = {}
    doc_info = ''
    
    @classmethod
    def load_code_dict(cls, c = '<br>'):
        for e in cls.__dict__:
            v = cls.__dict__[e]
            if type(v) == tuple and type(v[0]) == int and type(v[1]) == str:
                cls.code_dict[v[0]] = v
                # add doc info
                cls.doc_info += "Msg:%s%sCode:%s%sInfo:%s%s" % (e, c, v[0], c, v[1], c*2)

    @classmethod
    def error(cls, code):
        if cls.code_dict.get(code):
            return cls.code_dict[code]
        return (SpuError.unknow_error, '未知错误')

Error.success = (code(), 'success')

Error.load_code_dict()

info = "Error Info:<br>%s" % Error.doc_info
setdoc(info)
