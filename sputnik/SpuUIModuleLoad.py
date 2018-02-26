#-*- coding: utf-8 -*
#
# Copyright 2011 msx.com
# by error.d@gmail.com
# 2012-2-20
#
# Sputnik Tornado UI Module Load 
#

import logging
from SpuUOM import SpuUOM

class SpuUIModule:
    ui_modules = {}
    
    @classmethod
    def LoadUIModule(cls, module_file):
        logging.debug('* Load UI Module: %s' % str(module_file))
        ui_modules = {}
        module = __import__(module_file)
        class_list = SpuUOM.get_class_list(module)
        for c in class_list:
            ui_modules[c.__name__] = c
            logging.debug("|\t-> Load UI Module: %s" % c.__name__)
        cls.ui_modules = ui_modules

    @classmethod
    def get_ui_modules(cls):
        return cls.ui_modules

