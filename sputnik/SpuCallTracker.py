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

import codecs
import inspect
import logging as s_logging
from SpuHook import SpuHookEngine, HookHandler
from SpuUtil import to_unicode

def logging(msg):
    msg = "[CallTracker]*{*%s*}*" % msg
    s_logging.debug(msg)

class CallTrackerHandler(HookHandler):
    _c_call_level = 0
    _c_caller_num = 0

    _c_tracker_file = None

    def __init__(self, level_space_num=2):
        super(CallTrackerHandler, self).__init__()
        self._level_space_num = level_space_num
        self._caller_id = self.make_caller_id()

    @classmethod
    def open_tracker_file(cls, tracker_file):
        if tracker_file:
            cls._c_tracker_file = codecs.open(tracker_file, 'w', encoding='utf8')

    @classmethod
    def close_tracker_file(cls):
        if cls._c_tracker_file:
            cls._c_tracker_file.close()

    @classmethod
    def make_caller_id(cls):
        CallTrackerHandler._c_caller_num += 1
        return CallTrackerHandler._c_caller_num

    @classmethod
    def enter_call(cls):
        cls._c_call_level += 1

    @classmethod
    def exit_call(cls):
        cls._c_call_level -= 1

    @classmethod
    def call_level(cls):
        return cls._c_call_level

    def caller_id(self):
        return self._caller_id

    def space(self):
        return ' ' * self._level_space_num * self.call_level()

    def track_log(self, msg):
        if self._c_tracker_file:
            msg = to_unicode("%s\n" % msg)
            self._c_tracker_file.write(msg)
        else:
            logging(msg)

    def fv(self, arg_value):
        if type(arg_value) is str:
            arg_value = '"%s"' % arg_value
        elif type(arg_value) is unicode:
            arg_value = 'u"%s"' % arg_value
        return arg_value

    def args_info(self, arg_values):

        args_def = self.args_def()

        args_dict = {}
        args_list = []
        kwargs_dict = {}
        _args = args_def.args
        _default_arg_values = args_def.defaults
        _runtime_args_values = list(arg_values.locals['args'])

        # first add default arg
        if _default_arg_values:
            for key, value in zip(_args[::-1], _default_arg_values[::-1]):
                args_dict[key] = value

        # add common arg, duplication of name overwrite default arg
        for key, value in zip(_args, _runtime_args_values):
            args_dict[key] = value
        
        # add args
        clen = len(args_def.args)
        args_list = list(_runtime_args_values[clen:])

        # add kwargs
        kwargs_dict = arg_values.locals['kwargs']

        # assembly args expression
        info = []
        # class method and exist self, append self 
        if self.hook_type() == HookHandler.Method and \
               'self' in args_dict:
            c_self = str(args_dict['self'].__class__)
            info.append("self=%s" % c_self)
            del args_dict['self']

        for arg_name, arg_value in args_dict.items():
            info.append("%s=%s" % (arg_name, self.fv(arg_value)))

        if args_list:
            info.append("*args=[%s]" % ', '.join(map(str, map(self.fv, args_list))))

        if kwargs_dict:
            info.append("**kwargs=[%s]" % \
                        ', '.join(["%s=%s" % (k, self.fv(v)) \
                                   for k,v in kwargs_dict.items() \
                                   if k not in args_dict]))

        return "(%s)" % (', '.join(info))

    def call_info(self, arg_values, *args, **kwargs):
        info = []
        if self.class_name():
            info.append('%s.' % self.class_name())
        info.append(self.function_name())
        info.append(self.args_info(arg_values))
        return ''.join(info)

    def call(self, hook_type, hook_object, call_frame,
             *args, **kwargs):
        self.enter_call()
        arg_values = inspect.getargvalues(call_frame)
        # prevent recursive call
        self.hook_handler_disabled()
        self.track_log("%s[%s]-> %s" % (self.space(), self.caller_id(),
                                        self.call_info(arg_values, *args, **kwargs)))
        self.hook_handler_enabled()

    def result(self, r):
        self.track_log("%s<-[%s] return %s\n" % (self.space(), self.caller_id(),
                                                 self.fv(r)))
        self.exit_call()
        return r

class CallTrackerEngine(SpuHookEngine):
    def __init__(self, tracker_file='./call_tracker.log',
                 import_module=None):
        super(CallTrackerEngine, self).__init__(import_module,
                                                CallTrackerHandler)
        CallTrackerHandler.open_tracker_file(tracker_file)

    def __del__(self):
        CallTrackerHandler.close_tracker_file()

    def calltrack_module(self, module, import_module=None):
        self.hook_module(module, import_module, CallTrackerHandler)
