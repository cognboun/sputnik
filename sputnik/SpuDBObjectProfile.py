#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 msx.com
# Copyright 2013 msx.com
# Copyright 2014 lrzm.com
# by error.d@gmail.com
# 2014-9-18
#
# SpuDBObject Sql Profile
#

import inspect
import logging as s_logging

def logging(msg):
    msg = "[SDBProfile]*{*%s*}*" % msg
    s_logging.debug(msg)

class ProfileHandler(object):
    def __init__(self, class_name, func_name):
        self._class_name = class_name
        self._func_name = func_name

    def get_hook_class_name(self):
        return self._class_name

    def get_hook_func_name(self):
        return self._func_name
    

class Dispatch(object):
    def __init__(self, func):
        self._func = func

    def __call__(self, func_self, *args, **kwargs):
        logging("call function:%s args: %s kwargs: %s" % (self._func,
                                                          args, kwargs))
        return self._func(func_self, *args, **kwargs)

class SpuDBObjectProfile(object):

    #
    # ** Start Profile
    #
    _c_profile = False

    @classmethod
    def set_profile(cls, is_profile):
        cls._c_profile = is_profile

    def __init__(self, profile_handler_list=[]):
        self._profile_handler_list = profile_handler_list

    def _get_class_list(self, m):
        class_list = []
        class_strlist = dir(m)
        for c in class_strlist:
            obj = m.__dict__[c]
            # remove import symbol
            if inspect.getmodule(obj) == m and inspect.isclass(obj):
                class_list.append(obj)
        return class_list

    def _get_method_list(self, c):
        method_list = []
        method_strlist = dir(c)
        for method in method_strlist:
            if method[0] == '_':
                continue
            obj = c.__dict__.get(method, None)
            if not obj:
                continue
            if inspect.isfunction(obj):
                method_list.append(obj)
        return method_list

    def _is_hook(self, _class, func):
        return True

    def add_hook(self, profile_handler):
        self._profile_handler_list.append(profile_handler)

    def profile(self, func):
        if not self._c_profile:
            return func

        func_info = "module:%s func:%s" % (func.__module__,
                                           func.__name__)
        logging("profile hook %s" % func_info)
        def func_obj_call(func_self, *args, **kwargs):
            dispatch = Dispatch(func)
            return dispatch(func_self, *args, **kwargs)
        return func_obj_call

    def module_profile(self, module):
        if not self._c_profile:
            return
        logging("profile module %s" % module)
        [[setattr(_class, method.__name__, self.profile(method)) \
          for method in self._get_method_list(_class) \
          if self._is_hook(_class, method)] for _class in self._get_class_list(module)]

SDBProfile = SpuDBObjectProfile()
SDBProfile.set_profile(True)
