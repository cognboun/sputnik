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
import hook_module

Hook.hook_module(hook_module)
hook_module.test_hook('123414')
hook_module.test_main()

