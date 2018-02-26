#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 msx.com
# Copyright 2013 msx.com
# Copyright 2014 lrzm.com
# by error.d@gmail.com
# 2014-9-17
#
# Sputnik hOok enGine
#

import re
import inspect
import logging as s_logging
from pprint import pprint
from sputnik.SpuException import UnSupportHookOBject

def logging_info(msg):
    return "[SpuHook]*{*%s*}*" % msg

def error(msg):
    s_logging.error(logging_info(msg))

def logging(msg):
    s_logging.debug(logging_info(msg))

class HookHandler(object):
    Unknow = 'Unknow'
    Function = 'Function'
    Method = 'Method'
    ClassMethod = 'ClassMethod'

    _hook_enabled = True

    @classmethod
    def hook_handler_enabled(cls):
        cls._hook_enabled = True

    @classmethod
    def hook_handler_disabled(cls):
        cls._hook_enabled = False
    
    def __init__(self):
        self._hook_type = self.Unknow
        self._hook_object = None
        self._module_name = None
        self._class_name = None
        self._function_name = None
        self._args_def = None

    def _handler_call(self, call_frame, *args, **kwargs):
        hook_type = self.hook_type()
        hook_object = self.hook_object()
        logging("[call %s:%s:%s hook handler %s]" % (self._module_name,
                                                     self._class_name,
                                                     self._function_name,
                                                     self))
        
        hook_status = self.call(hook_type,
                                hook_object,
                                call_frame,
                                *args, **kwargs)
        result = hook_object(*args, **kwargs)
        result = self.result(result)
        return result

    def __call__(self, call_frame, *args, **kwargs):
        if self._hook_enabled:
            return self._handler_call(call_frame, *args, **kwargs)
        return self.hook_object()(*args, **kwargs)

    def _set_hook_type(self, t):
        self._hook_type = t

    def _set_hook_object(self, hook_object):
        self._hook_object = hook_object

    def _set_object_info(self, module_name, class_name, function_name,
                         args_info):
        self._module_name = module_name
        self._class_name = class_name
        self._function_name = function_name
        self._args_def = args_info

    def hook_type(self):
        return self._hook_type

    def hook_object(self):
        return self._hook_object

    def module_name(self):
        return self._module_name

    def class_name(self):
        return self._class_name

    def function_name(self):
        return self._function_name

    def args_def(self):
        return self._args_def

    def call(self, hook_type, hook_object, call_frame,
             *args, **kwargs):
        raise NotImplementedError

    def result(self, r):
        return r

class DefaultHookHandler(HookHandler):
    def __init__(self):
        super(DefaultHookHandler, self).__init__()

    def call(self, hook_type, hook_object, call_frame,
             *args, **kwargs):
        logging('[default %s hook handler][%s]' \
                '[args:%s][kwargs:%s]' % (hook_type,
                                          hook_object,
                                          args,
                                          kwargs))
    def result(self, r):
        logging('[default %s hook handler][%s][result:%s]' % (self.hook_type(),
                                                              self.hook_object(),
                                                              r))
        return r

class SpuHookEngine(object):

    def __init__(self, import_module=None,
                 default_hook_handler=DefaultHookHandler):
        self._c_hook = True
        self._import_module = import_module
        self._default_hook_handler = default_hook_handler

    def _get_class_and_function_list(self, m):
        symbol_list = []
        class_strlist = dir(m)
        for c in class_strlist:
            obj = m.__dict__[c]
            # remove import symbol
            if inspect.getmodule(obj) == m:
                if (inspect.isclass(obj) and not issubclass(obj, HookHandler)) or \
                       inspect.isfunction(obj):
                    symbol_list.append(obj)
        return symbol_list

    def _get_method_list(self, c):
        method_list = []
        method_strlist = dir(c)
        for method in method_strlist:
            obj = c.__dict__.get(method, None)
            if not obj:
                continue
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                method_list.append(obj)
        return method_list

    def _get_class_name(self, _class):
        rules = []
        _class = str(_class)
        rules.append((re.match('.*<.*\'(.+?)\'>.*', _class), 1))
        rules.append((re.match('\.?(.+?)+', _class), 0))
        try:
            for _class_name, idx in rules:
                if _class_name:
                    _class_name = _class_name.group(idx)
                    break
        except Exception as m:
            error("Get class name (%s) failed: %s" % (_class, m))
            return 'Unknow'
        return _class_name.split('.')[-1]

    def _hook_function(self, func, hook_handler, _class=None):
        module_name = func.__module__
        func_name = func.__name__
        class_name = None

        if _class:
            class_name = self._get_class_name(_class)
            hook_type = HookHandler.Method
            hook_info = "module:%s class:%s method:%s" % (module_name,
                                                          class_name,
                                                          func_name)
            

        else:
            hook_type = HookHandler.Function
            hook_info = "module:%s function:%s" % (module_name,
                                                   func_name)
        logging("hook [%s]" % hook_info)
        handler = hook_handler()
        handler._set_hook_type(hook_type)
        handler._set_hook_object(func)
        handler._set_object_info(module_name, class_name, func_name,
                                 inspect.getargspec(func))
        def func_obj_call(*args, **kwargs):
            return handler(inspect.currentframe(), *args, **kwargs)
        return func_obj_call

    def _hook_class(self, _class, hook_handler):
        logging("hook class [%s]" % _class)

        [setattr(_class, method.__name__,
                 self._hook_object(method, hook_handler, _class=_class)) \
         for method in self._get_method_list(_class)]

        return _class
        
    def _hook_object(self, hook_object, hook_handler, _class=None):
        if inspect.isclass(hook_object):
            return self._hook_class(hook_object, hook_handler)
        elif inspect.isfunction(hook_object):
            return self._hook_function(hook_object, hook_handler, _class=_class)
        else:
            raise UnSupportHookOBject(hook_object)

    def _hook_default_hook_handler(self, hook_object):
        if not self._c_hook:
            return hook_object
        return self._hook_object(hook_object, self._default_hook_handler)

    def _hook_user_hook_handler(self, hook_handler):
        def hook_wrapper(hook_object):
            if not self._c_hook:
                return hook_object
            return self._hook_object(hook_object, hook_handler)
        return hook_wrapper

    def hook(self, hook_param):
        """
        hook : class
               function

        todo: classmethod
              class in class
        """
        if inspect.isclass(hook_param) and issubclass(hook_param, HookHandler):
            return self._hook_user_hook_handler(hook_param)
        return self._hook_default_hook_handler(hook_param)

    def hook_module(self, module, import_module=None,
                    hook_handler=DefaultHookHandler):
        """
        
        """
        
        if not self._c_hook:
            return

        # import order import_module -> self._import_module -> module
        import_module = import_module if import_module else self._import_module
        import_module = import_module if import_module else module
        logging("hook module %s" % module)
        for symbol in self._get_class_and_function_list(module):
            new_func = self._hook_object(symbol, hook_handler)
            setattr(import_module, symbol.__name__, new_func)
            if import_module is not module:
                setattr(module, symbol.__name__, new_func)

SpuHook = SpuHookEngine()
