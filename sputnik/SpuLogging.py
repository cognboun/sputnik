#-*- coding: utf-8 -*
#
# Copyright 2011 msx.com
# by error.d@gmail.com
# 2012-3-7
#
# Sputnik Logging
#
# ToDoList:
# 

import os
import sys
import thread
import logging
import logging.handlers
import time
from SpuUtil import *

try:
    import curses
except ImportError:
    curses = None


logging_config = None

## from logging

def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        return sys.exc_info()[2].tb_frame.f_back

if hasattr(sys, '_getframe'): currentframe = lambda: sys._getframe()

## from tornado 3.x

# Fake unicode literal support:  Python 3.2 doesn't have the u'' marker for
# literal strings, and alternative solutions like "from __future__ import
# unicode_literals" have other problems (see PEP 414).  u() can be applied
# to ascii strings that include \u escapes (but they must not contain
# literal non-ascii characters).
if type('') is not type(b''):
    def u(s):
        return s
    unicode_type = str
    basestring_type = str
else:
    def u(s):
        return s.decode('unicode_escape')
    unicode_type = unicode
    basestring_type = basestring

def _stderr_supports_color():
    color = False
    if curses and hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
        try:
            curses.setupterm()
            if curses.tigetnum("colors") > 0:
                color = True
        except Exception:
            pass
    return color

def _safe_unicode(s):
    try:
        return unicode(s)
    except UnicodeDecodeError:
        return repr(s)

class SputnikLogFormatter(logging.Formatter):
    """Log formatter used in Tornado.

    Key features of this formatter are:

    * Color support when logging to a terminal that supports it.
    * Timestamps on every log line.
    * Robust against str/bytes encoding problems.

    This formatter is enabled automatically by
    `tornado.options.parse_command_line` (unless ``--logging=none`` is
    used).
    """
    DEFAULT_FORMAT = '%(color)s[%(levelname)1.1s %(asctime)s.%(msecs)d %(filename)s:%(funcName)s:%(lineno)d %(thread)d]%(end_color)s %(message)s'
    DEFAULT_DATE_FORMAT = '%y%m%d %H:%M:%S'
    DEFAULT_COLORS = {
        logging.DEBUG: 4,  # Blue
        logging.INFO: 2,  # Green
        logging.WARNING: 3,  # Yellow
        logging.ERROR: 1,  # Red
    }

    def __init__(self, color=True, fmt=DEFAULT_FORMAT,
                 datefmt=DEFAULT_DATE_FORMAT, colors=DEFAULT_COLORS):
        r"""
        :arg bool color: Enables color support.
        :arg string fmt: Log message format.
          It will be applied to the attributes dict of log records. The
          text between ``%(color)s`` and ``%(end_color)s`` will be colored
          depending on the level if color support is on.
        :arg dict colors: color mappings from logging level to terminal color
          code
        :arg string datefmt: Datetime format.
          Used for formatting ``(asctime)`` placeholder in ``prefix_fmt``.

        .. versionchanged:: 3.2

           Added ``fmt`` and ``datefmt`` arguments.
        """
        logging.Formatter.__init__(self, datefmt=datefmt)
        self._fmt = fmt

        self._app_log = True
        self._colors = {}
        if color and _stderr_supports_color():
            # The curses module has some str/bytes confusion in
            # python3.  Until version 3.2.3, most methods return
            # bytes, but only accept strings.  In addition, we want to
            # output these strings with the logging module, which
            # works with unicode strings.  The explicit calls to
            # unicode() below are harmless in python2 but will do the
            # right conversion in python 3.
            fg_color = (curses.tigetstr("setaf") or
                        curses.tigetstr("setf") or "")
            if (3, 0) < sys.version_info < (3, 2, 3):
                fg_color = unicode_type(fg_color, "ascii")

            for levelno, code in colors.items():
                self._colors[levelno] = unicode_type(curses.tparm(fg_color, code), "ascii")
            self._normal = unicode_type(curses.tigetstr("sgr0"), "ascii")
        else:
            self._normal = ''

    def off_app_log(self):
        self._app_log = False

    def on_app_log(self):
        self._app_log = True

    def format(self, record):
        try:
            message = record.getMessage()
            assert isinstance(message, basestring_type)  # guaranteed by logging
            # Encoding notes:  The logging module prefers to work with character
            # strings, but only enforces that log messages are instances of
            # basestring.  In python 2, non-ascii bytestrings will make
            # their way through the logging framework until they blow up with
            # an unhelpful decoding error (with this formatter it happens
            # when we attach the prefix, but there are other opportunities for
            # exceptions further along in the framework).
            #
            # If a byte string makes it this far, convert it to unicode to
            # ensure it will make it out to the logs.  Use repr() as a fallback
            # to ensure that all byte strings can be converted successfully,
            # but don't do it by default so we don't add extra quotes to ascii
            # bytestrings.  This is a bit of a hacky place to do this, but
            # it's worth it since the encoding errors that would otherwise
            # result are so useless (and tornado is fond of using utf8-encoded
            # byte strings whereever possible).
            record.message = _safe_unicode(message)
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)

        record.asctime = self.formatTime(record, self.datefmt)

        if record.levelno in self._colors:
            record.color = self._colors[record.levelno]
            record.end_color = self._normal
        else:
            record.color = record.end_color = ''

        frame = currentframe()
        (filename, lineno, funname, module) = SpuLogging.get_app_call_info(frame, self._app_log)
        record.__dict__['filename'] = filename
        record.__dict__['lineno'] = int(lineno)
        record.__dict__['funcName'] = funname

        # thread id
        record.__dict__['tid'] = thread.get_ident()
        
        formatted = self._fmt % record.__dict__

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            # exc_text contains multiple lines.  We need to _safe_unicode
            # each line separately so that non-utf8 bytes don't cause
            # all the newlines to turn into '\n'.
            lines = [formatted.rstrip()]
            lines.extend(_safe_unicode(ln) for ln in record.exc_text.split('\n'))
            formatted = '\n'.join(lines)
        return formatted.replace("\n", "\n    ")

def _start_error_log_tracking(path,
                             maxBytes,
                             backupCount
                             ):
    hdlr = logging.handlers.RotatingFileHandler(
        filename=path,
        maxBytes=maxBytes,
        backupCount=backupCount)
    hdlr.setFormatter(SputnikLogFormatter(color=False))
    hdlr.setLevel(logging.ERROR)
    logger = logging.getLogger()
    logger.addHandler(hdlr)

g_sputnik_log_formatter = []

def _use_sputnik_logformat():
    logger = logging.getLogger()
    for handler in logger.handlers:
        color = True
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            color = False
        slf = SputnikLogFormatter(color=color)
        handler.setFormatter(slf)
        g_sputnik_log_formatter.append(slf)

def start_sputnik_logging(use_sputnik_logformat=True,
                          start_error_log_tracking=True,
                          error_log_path='./error.log',
                          maxBytes=100 * 1000 * 1000,
                          backupCount=10
                          ):
    if use_sputnik_logformat:
        _use_sputnik_logformat()
    if start_error_log_tracking:
        _start_error_log_tracking(error_log_path, maxBytes, backupCount)

def off_app_log():
    for slf in g_sputnik_log_formatter:
        slf.off_app_log()

def on_app_log():
    for slf in g_sputnik_log_formatter:
        slf.on_app_log()

class AppLog():
    def __init__(self, app_log):
        self._app_log = app_log

    def __enter__(self):
        if self._app_log is False:
            off_app_log()

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self._app_log is False:
            on_app_log()
        return True

class SpuLoggingMemBuff:
    def __init__(self):
        self.clear()

    def clear(self):
        self.logs = ''

    def log(self, log):
        self.logs += log + '\n'

    def get_logs(self):
        return self.logs

class SpuLogging:
    log_slow = True
    log_slow_time = 500
    membuff = SpuLoggingMemBuff()
    log_status_slow = 0x1
    log_status_function = 0x2

    _c_logging_config = None

    @classmethod
    def setting(cls, logging_config):
        cls._c_logging_config = logging_config

    def __init__(self, 
                 module_name = '', 
                 class_name = '', 
                 function_name = '', 
                 tag_name = '',
                 app_log=True):
        self._module = module_name
        self._class = class_name
        self._function = function_name
        self._tag = tag_name
        self._app_log = app_log

        self._load_config()


    def _load_config(self):
        logging.debug("%s.%s.%s Use Logging Config" % (
            self._module, self._class, self._function))
        assert SpuLogging._c_logging_config, "Please first import " \
               "sputnik.sputnik_init and call sputnik_init "\
               "setting logging config"
        config = SpuLogging._c_logging_config
        SpuLogging.log_slow = int(config.get('log_slow',
                                             SpuLogging.log_slow))
        SpuLogging.log_slow_time = config.get('log_slow_time',
                                              SpuLogging.log_slow_time)
        self._log_function = config.get('log_function',
                                        None)
        self._flowpath_db_detail = config.get('flowpath_db_detail', False)
        self._flowpath_cache_detail = config.get('flowpath_cache_detail', False)        

    def set_module(self, module_name):
        self._module = module_name

    def set_class(self, class_name):
        self._class = class_name

    def set_function(self, function_name):
        self._function = function_name

    def set_tag(self, tag_name):
        self._tag = tag_name

    def set_class_func(self, class_name, function_name):
        self._class = class_name
        self._function = function_name

    def make_msg_info(self, t, a1, a2, a3, a4, *args):
        if not a1:
            a1 = str(self._module)
        if not a2:
            a2 = str(self._class)
        if not a3:
            a3 = str(self._function)
        if not a4:
            a4 = str(self._tag)
        info = [
            '[', t, ']'
            '[', a1, ']',
            '[', a2, ']',
            '[', a3, ']',
            '[', a4, ']',
            ]
        for arg in args:
            info.append(''.join(('*{*', to_text(arg), '*}*')))
        return ''.join(info)

    @classmethod
    def info(cls, msg, *args, **kwargs):
        app_log = kwargs.get('app_log', True)
        if 'app_log' in kwargs: del kwargs['app_log']
        with AppLog(app_log):
            logging.info(to_text(msg), *args, **kwargs)

    @classmethod
    def warn(cls, msg, *args, **kwargs):
        app_log = kwargs.get('app_log', True)
        if 'app_log' in kwargs: del kwargs['app_log']        
        with AppLog(app_log):
            logging.warn(to_text(msg), *args, **kwargs)

    @classmethod
    def debug(cls, msg, *args, **kwargs):
        app_log = kwargs.get('app_log', True)
        if 'app_log' in kwargs: del kwargs['app_log']
        with AppLog(app_log):
            logging.debug(to_text(msg), *args, **kwargs)

    @classmethod
    def error(cls, msg, *args, **kwargs):
        app_log = kwargs.get('app_log', True)
        if 'app_log' in kwargs: del kwargs['app_log']        
        with AppLog(app_log):
            logging.error(to_text(msg), *args, **kwargs)

    @classmethod
    def spu_info(cls, msg, *args, **kwargs):
        cls.info(msg, app_log=False, *args, **kwargs)

    @classmethod
    def spu_warn(cls, msg, *args, **kwargs):
        cls.warn(msg, app_log=False, *args, **kwargs)

    @classmethod
    def spu_debug(cls, msg, *args, **kwargs):
        cls.debug(msg, app_log=False, *args, **kwargs)

    @classmethod
    def spu_error(cls, msg, *args, **kwargs):
        cls.error(msg, app_log=False, *args, **kwargs)

    @classmethod
    def slow(cls, msg):
        cls.membuff.log(to_text(msg))
    
    @classmethod
    def slow_clear(cls):
        cls.membuff.clear()
        cls.slow('[SlowLog]')

    @classmethod
    def get_slowlog(cls):
        return cls.membuff.get_logs()

    @classmethod
    def show_slowlog(cls, process_time, app_log=False):
        if cls.log_slow and process_time >= cls.log_slow_time:
            cls.info(cls.membuff.get_logs(), app_log=app_log)
        cls.slow_clear()

    @classmethod
    def get_app_call_info(cls, frame, app_log=True):
        """
        return : (filename, lineno, funtionname, module)
        """
        lineno = 0
        function = ''
        while frame:
            filename = frame.f_code.co_filename
            if ('logging' not in filename and
                'SpuLogging' not in filename and
                'tornado' not in filename and 
                (not app_log or 'Spu' not in filename)):
                lineno = frame.f_lineno
                function = frame.f_code.co_name
                break
            frame = frame.f_back
        return (str(filename).split('/')[-1], str(lineno), str(function), None)

    @classmethod
    def error_dump_frame(cls, msg):
        frame = sys._getframe()
        frame_list = ['Error Info And Frames: %s\n' % msg]
        while frame:
            filename = frame.f_code.co_filename.split('/')[-1]
            line = frame.f_lineno
            function = frame.f_code.co_name
            frame_list.append("\t%s:%s:%s\n" % (filename, line, function))
            frame = frame.f_back
        msg = to_text(''.join(frame_list))
        cls.error(msg)

    def _log_status(self, type, function):
        status = 0
        if self.log_slow:
            status |= self.log_status_slow
        if self._log_function and \
               (self._log_function['all'] or
                self._log_function[type]['all'] or
                self._log_function[type][function]):
            status |= self.log_status_function
        return status

    def _show_log(self, status, log, app_log=None):
        if status & self.log_status_function:
            self.info(log, app_log=self._app_log if app_log is None else app_log)
        if status & self.log_status_slow:
            self.slow(log)

    def flowpath(self, msg, app_log=True):
        status = self._log_status('flowpath', 'flowpath')
        if not status:
            return
        msg = to_text(msg)
        log = self.make_msg_info('Flowpath', None, None, None, None, msg)
        self._show_log(status, log, app_log)

    def flowpath_logic(self, tag, app_log=True, *args):
        status = self._log_status('flowpath', 'logic')
        if not status:
            return
        _tag = self._tag
        self._tag = tag
        log = self.make_msg_info('FlowpathLogic', None, None, None, None, *args)
        self._tag = _tag
        self._show_log(status, log, app_log)

    def flowpath_service(self, msg, app_log=None):
        pass

    def flowpath_db(self, msg, perf_t=None, data=None, app_log=True):
        if perf_t:
            self.perf_db(msg, perf_t)
        status = self._log_status('flowpath', 'db')
        if not status:
            return

        msg = to_text(msg)
        if self._flowpath_db_detail:
            log = self.make_msg_info('FlowpathDb', None, None, None, None, msg,
                                     to_text(data))
        else:
            log = self.make_msg_info('FlowpathDb', None, None, None, None, msg)
        self._show_log(status, log, app_log=app_log)

    def flowpath_cache(self, func, key, value, tag,
                       perf_t=None, app_log=True):
        if perf_t:
            self.perf_cache(func, key, tag, perf_t)
        status = self._log_status('flowpath', 'cache')
        if not status:
            return
        if self._flowpath_cache_detail:
            log = self.make_msg_info('FlowpathCache', None, None, func,
                                     tag, key, to_text(value))
        else:
            log = self.make_msg_info('FlowpathCache', None, None, func,
                                     tag, key)
        self._show_log(status, log, app_log=app_log)

    def perf(self, msg, debugtime, app_log=True):
        status = self._log_status('perf', 'perf')
        if not status:
            return
        log = self.make_msg_info('Perf', None, None, None, None, msg, debugtime)
        self._show_log(status, log, app_log=app_log)

    def perf_func(self, fun_name, debugtime, app_log=True):
        status = self._log_status('perf', 'func')
        if not status:
            return
        self.set_function(fun_name)
        log = self.make_msg_info('PerfFunc', None, None, None, None, debugtime)
        self._show_log(status, log, app_log=app_log)

    def perf_service(self, service_name, msg, app_log=True):
        pass

    def perf_db(self, sql, debugtime, app_log=True):
        status = self._log_status('perf', 'db')
        if not status:
            return

        log = self.make_msg_info('PerfDb', None, None, None, None, sql, debugtime)
        self._show_log(status, log, app_log=app_log)

    def perf_cache(self, func, key, tag,
                   debugtime, app_log=True):
        status = self._log_status('perf', 'cache')
        if not status:
            return
        log = self.make_msg_info('PerfCache', None, None, func,
                                 tag, key, debugtime)
        self._show_log(status, log, app_log=app_log)
