#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-17
#

import sys
import re
import tornado.web
import SpuConfig
import SpuSession
from SpuPythonObject import *
from SpuUtil import *
from SpuDateTime import *
from SpuUrl import *
from SpuUOM import *
from SpuLogging import *
from SpuFactory import SpuDOFactory
from SpuCacheManager import SpuCacheManager
from SpuDataFormat import SpuDataFormat
from SpuDomainManager import SpuDomainManager

auto_session_engine = SpuSession.get_session_engine

def set_auto_session_engine(session_engine):
    global auto_session_engine
    auto_session_engine = session_engine

def debug_log_write_client(self):
    if self._debug:
        slowlog = SpuLogging.get_slowlog()
        slowlog = "<br><br><br>%s" % slowlog.replace('\n', '<br><br>')
        self.tornado.write(slowlog)

def pre_request(func):
    def request_process(self, *args, **kwargs):
        self._init_handler()
        SpuLogging.slow_clear()

        self._init_spu_argument()
        s_time = time.time()
        self._get_session()

        r = func(self, *args, **kwargs)

        self._save_session()
        self._process_handler_result()
        process_time = self._process_time(s_time, time.time())
        debug_log_write_client(self)
        SpuLogging.show_slowlog(process_time)
        
        return r
    
    return request_process

class ArgDict(dict):
    def del_key(self, key):
        del self[key]

    def dict(self):
        return self

class SpuRequestHandler:
    context = None

    _logging = SpuLogging(module_name = 'SpuRequestHandler',
                          class_name = 'SpuRequestHandler',
                          app_log=False)

    @classmethod
    def set_context(cls, context):
        SpuRequestHandler.context = context

    def __init__(self):
        self.tornado = None
        self.rule = None
        self.session = None
        self.process_obj = None
        self._render_html_template = False
        self._template = None
        self._pyobj = None

    def _set_tornado(self, tornado):
        self.tornado = tornado
    
    def _set_rule(self, rule):
        self.rule = rule

    def _set_session(self, session):
        self.session = session

    def _get_session(self):
        return self.session

    @property
    def _context(self):
        return SpuRequestHandler.context

    def _arg_str(self, arg, default):
        s = self._arg(arg, str, None)
        if s:
            return s
        return self._arg(arg, unicode, default)

    def _arg_unicode(self, arg, default):
        if type(arg) == unicode:
            return arg
        try:
            unc = to_unicode(arg)
        except Exception as m:
            self._logging.spu_error("[Error] Arg Unicode: %s " % m)
            if not default:
                return default
            return unicode(default)
        if not arg:
            return unicode(default)
        return unc

    def _arg(self, arg, type, default):
        if not arg:
            return default
        try:
            arg = type(arg)
        except Exception:
            arg = default
        return arg

    def _file(self, file_key):
        return self.tornado.request.files.get(file_key, None)
    
    def _files(self):
        return self.tornado.request.files

    def _check_arg(self, *args):
        for arg in args:
            if arg == None:
                return False
        return True

    def _render(self, pyobject):
        r = SpuDataFormat.format(pyobject,
                                 self.tornado._format,
                                 self.tornado._format_argument)
        return r

    def _write(self, r):
        if SpuConfig.SpuDebug:
            self._logging.spu_debug("[Response]: %s" % r)
        self.tornado.write(r)

    def _response(self, pyobject):
        r = self._render(pyobject)
        self._write(r)

    def _html_render_list(self, template, pyobjectlist, append_info = {}):
        pyobj = PyobjectList((0,''), pyobjectlist, append_info)
        if self.tornado._format not in (None, ""):
            return self._response(pyobj)
        self._set_html_template_render(template, pyobj.python_object())

    def _html_render(self, template, pyobject, append_info = {}):
        pyobj = Pyobject((0,''), pyobject, append_info)
        if self.tornado._format not in (None, ""):
            return self._response(pyobj)
        self._set_html_template_render(template, pyobj.python_object())

    def _set_html_template_render(self, template, pyobj):
        self._render_html_template = True
        self._template = template
        self._pyobj = pyobj

    def _unset_html_template_render(self):
        self._render_html_template = False
        self._template = None
        self._pyobj = None

    def _real_html_render(self):
        assert self._template and self._pyobj, "Not Template Or Pyobject"
        url = SpuUrlGenerator(self.rule.get_url_mod())
        if SpuConfig.SpuDebug:
            self._logging.spu_debug("[Response]: %s" % self._pyobj)
        self.tornado.render(self._template,
                            context=self._context,
                            pyobject=self._pyobj,
                            url=url,
                            tornado=self.tornado,
                            session=self.session,
                            domain=SpuDomainManager.get_domaindict())

    def _direct_write(self, r):
        self.tornado.write(r)

    def _error_404(self):
        default_msg = '404'
        if hasattr(self, '_error_handle__404'):
            self._error_handle__404()
            if SpuConfig.SpuDebug:
                self._logging.spu_debug("[RequestError]: %s" % default_msg)
            return
        self._write(default_msg)

    def _error_500(self):
        default_msg = '500'
        if hasattr(self, '_error_handle__500'):
            self._error_handle__500()
            if SpuConfig.SpuDebug:
                self._logging.spu_debug("[RequestError]: %s" % default_msg)
            return
        self._write(default_msg)

    def _error_missing_parameter(self, tornado, arg):
        default_msg = 'Missing Parameter: %s' % arg
        if hasattr(self, '_error_obj__missing_parameter'):
            self._error_obj__missing_parameter._set_tornado(tornado)
            self._error_obj__missing_parameter._error_handle__missing_parameter(arg)
            if SpuConfig.SpuDebug:
                self._logging.spu_debug("[RequestError]: %s" % default_msg)
            return
        self._write(default_msg)

    def _error_parameter_type_failed(self, tornado, arg, value, t):
        default_msg = 'Parameter Type Failed: arg(%s) value(%s) ' \
                      'expect type(%s) no (%s)' % \
                      (arg, value, get_type_str(t), get_type_str(type(value)))

        if hasattr(self, '_error_obj__parameter_type_failed'):
            self._error_obj__parameter_type_failed._set_tornado(tornado)
            self._error_obj__parameter_type_failed._error_handle__parameter_type_failed(
                arg, value, type)
            if SpuConfig.SpuDebug:
                self._logging.spu_debug("[RequestError]: %s" % default_msg)
            return

        self._write(default_msg)

    def _error_html_render_error(self, tornado):
        default_msg = 'Html Render Error'
        if hasattr(self, '_error_obj__html_render_error'):
            self._error_obj__html_render_error._set_tornado(tornado)
            self._error_obj__html_render_error._error_handle__html_error()
            if SpuConfig.SpuDebug:
                self._logging.spu_debug("[RequestError]: %s" % default_msg)
            return
        self._write(default_msg)

    def _error_process_error(self, tornado, m):
        if hasattr(self, '_error_obj__process_error'):
            self._error_obj__process_error._set_tornado(tornado)
            self._error_obj__process_error._error_handle__process_error()
            return

        s = str(m)
        r = re.search("got an unexpected keyword argument ('.+?')", s)
        if r:
            msg = "Unknow Argument %s" % r.groups()[0]
            return self._response(Pyobject((1, msg), None))
        else:
            msg = "[Error] Request Process: Unknow Error"
            return self._response(Pyobject((0, msg), None))
        
class SpuBaseHandler(tornado.web.RequestHandler,
                     SpuRequestHandler):

    _logging = SpuLogging(module_name='SpuRequest',
                          class_name='SpuBaseHandler',
                          app_log=False)
    
    def _get_auto_session_engine(self):
        return auto_session_engine

    def _process_error(self, m):
        self.tornado = self
        self._error_process_error(self, m)

    def process_debug(self, method, argdict):
        return self.processer(**argdict)

    def process_release(self, method, argdict):
        try:
            return self.processer(**argdict)
        except Exception as m:
            SpuLogging.spu_error('[%sProcessFailed]\n[%s]\n[%s]' % (
                method, 
                self._request_summary(),
                self.request),
                exc_info = True)
            return self._process_error(m)

    def processer(self):
        raise NotDefWebRequestProcesser()

    def get_arg_list(self):
        arglist = self.rule.get_args()
        return arglist

    def alignment_arg(self, args):
        arg_dict = self.rule.get_arg_dict()
        for arg in arg_dict:
            arg_info = arg_dict[arg]
            if type(arg_info) is dict:
                default = arg_info.get('adef', None)
            else:
                default = arg_info
            if not args.has_key(arg) or args.get(arg, None) is None:
                # set default value where has it, other set None
                if hasattr(args, 'set'):
                    args.set(arg, default)
                else:
                    args[arg] = default
            else:
                if type(arg_info) is not dict:
                    continue
                t = arg_info.get('atype', None)
                if t:
                    # type conversion failed and use default value,
                    # call error handler where no default value
                    if hasattr(args, 'get'):
                        in_arg = args.get(arg, None)
                    else:
                        in_arg = args[arg]
                    if in_arg is None and default is not None:
                        in_arg = default
                    try:
                        if t in (list, tuple):
                            if type(in_arg) not in (list, tuple):
                                if t is list:
                                    if in_arg is None:
                                        in_arg = []
                                    else:
                                        in_arg = [in_arg]
                                else:
                                    if in_arg is None:
                                        in_arg = tuple()
                                    else:
                                        in_arg = tuple(in_arg)
                        else:
                            in_arg = t(in_arg)
                    except Exception:
                        self._logging.spu_warn('Arg type conversion exception %s ' \
                                               'to %s' % (type(in_arg), t))
                        if default is not None:
                            in_arg = default
                        else:
                            if SpuConfig.SpuDebug:
                                if in_arg is None and default is None and t:
                                    self._logging.spu_debug('[AlignmentArgError]: ' \
                                                            'define type and not ' \
                                                            'define default value')
                                self._error_parameter_type_failed(self, arg, in_arg, t)
                            return False
                    if hasattr(args, 'set'):
                        args.set(arg, in_arg)
                    else:
                        args[arg] = in_arg
        return True

    def _post_file_arg(self, args):
        fname_list = self.rule._post_file
        if fname_list:
            for fname in fname_list:
                args[fname] = self.request.files.get(fname, None)

    def _get_url_obj(self, url):
        rule_mod = self.rule.get_url_mod()
        cls = create_url(rule_mod)
        obj = cls(url)
        if rule_mod == url_rule__path_and_value:
            obj.set_arg_list(self.get_arg_list())
        return obj

    def _check_arg_define(self, args):
        arg_dict = self.rule.get_arg_dict()
        for arg in arg_dict:
            arg_info = arg_dict[arg]
            if not arg_info:
                continue
            if type(arg_info) is dict and arg_info.get('aneed', False):
                v = args.get(arg, None)
                if v == '' or v == None:
                    self._error_missing_parameter(self, arg)
                    return False
        return True

    def _remove_notdefine_arg(self, args):
        if not hasattr(args, 'keys'):
            return

        if self.rule.get_arg_keywords():
            return

        arg_dict = self.rule.get_arg_dict()
        for arg in args.keys():
            if not arg in arg_dict:
                if hasattr(args, 'del_key'):
                    args.del_key(arg)
                else:
                    del args[arg]

    def _standardize_args(self, urlarg):
        # remove not define args
        self._remove_notdefine_arg(urlarg)

        # check args
        if not self._check_arg_define(urlarg):
            return False

        # alignment args and type conversion
        if not self.alignment_arg(urlarg):
            return False

        return True

    def _arg_process(self, args, arg):
        a = self.get_arguments(arg, None)
        c = len(a)
        if c == 1:
            a = a[0]
        elif c == 0:
            a = None
        args[arg] = a

    def _get_query_argument(self, req_args=None):
        if req_args:
            args = stringQ2B(req_args)
            urlarg = self._get_url_obj(req_args)
            urlarg.parse()
            self._urlarg = urlarg
            return urlarg

        args = ArgDict()
        # extract sputnik argument
        for spu_arg in self._get_all_spu_argument():
            self._arg_process(args, spu_arg)

        # extract argument list
        arglist = self.get_arg_list()
        for arg in arglist:
            self._arg_process(args, arg)

        # extract kwargs argument
        if self.rule.get_arg_keywords():
            arguments = None
            if hasattr(self.request, 'arguments'):
                arguments = self.request.arguments
            elif hasattr(self.request, 'query_arguments'):
                arguments = self.request.query_arguments
            else:
                assert 0, 'Unknow Tornado Request Arguments'

            for arg in arguments.keys():
                if arg not in arglist:
                    self._arg_process(args, arg)                    
        return args

    def _auto_session_enable(self):
        session_config = SpuConfig.SpuSession_Config
        auto_session_enable = session_config['auto_session_enable'] if session_config \
                              else False
        if SpuConfig.SpuDebug:
            self._logging.spu_debug("[Session]: Auto Session Enable: %s" % \
                                    auto_session_enable)
        return auto_session_enable

    # TODO: get cookie from url query
    def _get_session(self):
        session_config = SpuConfig.SpuSession_Config
        if not self._auto_session_enable():
            return
        session_id = self.get_cookie(session_config['session_cookie_name'], None)
        if SpuConfig.SpuDebug:
            self._logging.spu_debug("[Get Session]: Session Id: %s" % session_id)
        self.session = self._get_auto_session_engine()(session_key = session_id)
        
    def _save_session(self):
        session_config = SpuConfig.SpuSession_Config
        if not self._auto_session_enable():
            return
        try:
            modified = self.session.modified
        except AttributeError:
            if SpuConfig.SpuDebug:
                self._logging.spu_debug("[Save Session]: No Modified")
            pass
        else:
            if modified or session_config['session_save_every_request']:
                if self.session.get_expire_at_browser_close():
                    expires = None
                else:
                    expires = self.session.get_expiry_date()
                # Save the session data and refresh the client cookie.
                self.session.save()
                self.set_cookie(session_config['session_cookie_name'],
                                self.session.session_key,
                                domain=session_config['session_cookie_domain'],
                                expires=expires,
                                path=session_config['session_cookie_path'],
                                )
                if SpuConfig.SpuDebug:
                    self._logging.spu_debug("[Save Session]: " \
                                            "Session Id: %s expires: %s" % \
                                            (self.session.session_key, expires))
            else:
                if SpuConfig.SpuDebug:
                    self._logging.spu_debug("[Save Session]: " \
                                            "No Modified Session Id: %s" % \
                                            (self.session.session_key))
                pass


    def _process_handler_result_debug(self):
        if hasattr(self.processer_obj, '_render_html_template'):
            if self.processer_obj._render_html_template:
                self.processer_obj._real_html_render()

    def _process_handler_result_release(self):
        try:
            self._process_handler_result_debug()
        except Exception as m:
            self._error_html_render_error(self)

    def _process_handler_result(self):
        if SpuConfig.SpuDebug:
            self._process_handler_result_debug()
        else:
            self._process_handler_result_release()
        self.processer_obj._unset_html_template_render()

    def _process_time(self, s, e):
        """millisecond"""
        t = e - s
        ms = t * 1000
        ms = int(ms)
        return ms

    def _init_handler(self):
        self.tornado = self

    def _cut_long_arg(self, completelog, arg):
        if completelog:
            return arg

        new_arg = ""
        if arg and len(arg) > 1000:
            new_arg = arg[0:500] + " <<<<<<<<<<--- ............. --->>>>>>>>>> " + \
                      arg[-500:]
        else:
            new_arg = arg
        return new_arg

    def _get_all_spu_argument(self):
        return ('format', 'spudebug', 'jsonp_callback')

    def _init_spu_argument(self):
        self._format_argument = None

    def _process_jsonp_callback_argument(self):
        if self._jsonp_callback is not None:
            self._format = 'jsonp'
            self._format_argument = self._jsonp_callback

    def _get_process_spu_argument(self, urlarg):
        # process format
        self._format = urlarg.get('format')
        if urlarg.has_key('format'):
            urlarg.del_key('format')

        # process spudebug
        self._debug = urlarg.get('spudebug')
        if urlarg.has_key('spudebug'):
            urlarg.del_key('spudebug')

        # process jsonp_callback
        self._jsonp_callback = urlarg.get('jsonp_callback')
        self._process_jsonp_callback_argument()
        if urlarg.has_key('jsonp_callback'):
            urlarg.del_key('jsonp_callback')


    def _process_http_argument(self, args=None, post=False):
        http_argument = self._get_query_argument(args)
        self._get_process_spu_argument(http_argument)

        if post:
            self._post_file_arg(http_argument)

        if not self._standardize_args(http_argument):
            return None
        
        if type(http_argument) != dict:
            http_argument = http_argument.dict()
        return http_argument

    def _process_http_request(self, method, http_argument):
        if SpuConfig.SpuDebug:
            return self.process_debug(method, http_argument)
        else:
            return self.process_release(method, http_argument)

    #
    # Tornado Support Http Method
    #

    @pre_request
    def get(self, args=None):
        self._logging.set_function('get')
        self._logging.flowpath_logic('RequestQuery', self._request_summary())

        http_argument = self._process_http_argument(args=args)
        if http_argument is None:
            return

        self._logging.spu_info('[GetRequestArgs][%s]' % http_argument)

        return self._process_http_request('Get', http_argument)

    @pre_request
    def post(self):
        _complete_log = self.get_argument('completelog', None)
        self._logging.set_function('pos')
        self._logging.flowpath_logic('RequestQuery', self.request.path)
        self._logging.spu_debug(self._cut_long_arg(_complete_log,
                                                   'PostRequest: %s' % self.request))

        http_argument = self._process_http_argument(post=True)
        if http_argument is None:
            return

        self._logging.spu_info(self._cut_long_arg(_complete_log,
                                                  '[PostRequestArgs][%s]' % \
                                                  http_argument))
        
        return self._process_http_request('Post', http_argument)
