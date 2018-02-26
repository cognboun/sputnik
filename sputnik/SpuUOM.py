#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-17
#
# Sputnik Url Object Map
# 根据object的定义生成url规则
# 把url映射到object上
#
# http://xx.xx.xx/module/class/method/Argument1&Argument2&Argument3 
#    => module.class.method(Argument1, Argument2, Argument3)
#
# 使用时只需按制定规则创建module,class,method.而不用写url规则,系统可以
# 自动生成url规则,相应请求时根据url自动路由到制定module的指定class的指定method方法上，并传入参数
# * 非常适合提供api的应用。直接把类映射为api
# * 非常适合经常变更的web应用，只需要修改类即可，而无需修改url路由
#
# plan:
#  模块载入时执行UOM载入器
#  处理所有继承UOM基类的子类
#  处理所有公共方法
#  生成url规则(正则表达式)
#  post请求通过@POST装饰
#  post上传文件通过@POST_FILE修饰
#
# ToDoList:
# 参数对齐机制:
#  1. 根据函数定义，取得参数列表
#  2. 传入参数多出的删掉
#  3. 传入参数少的加入，值为None
#  4. 可以设置是否开启参数对齐机制
#
# 

import re
import logging
import inspect
import functools
import tornado.web
from SpuConfig import *
from SpuUrl import *
from SpuException import *
from SpuLogging import SpuLogging


"""arg info define
arg={aneed:False, atype:int, adef:10},
"""
atype = 'atype'  # arg type
adef = 'adef'   # arg default value
aneed = 'aneed' # need arg

def create_rule(type):
    # /module/class/method/args_name=value&args_name=value&args_name=value
    if type == url_rule__path_and_argument:
        return Rule_path_and_argument
    # /module/class/method?args_name=value&args_name=value&args_name=value
    elif type == url_rule__path_file_and_argument:
        return Rule_path_file_and_argument
    # /module/class-method-value-value-value-value
    elif type == url_rule__path_and_value:
        return Rule_path_and_value
    assert None, 'Unknow Rule Type'

def check_function_type(func):
    assert not (hasattr(func, 'post') and hasattr(func, 'url_rule')), "Post Function Not Use Url Rule"

def POST(func):
    func.post = True
    check_function_type(func)
    return func

def POST_FILE(*file_name):
    def g(func):
        func.post = True
        func.post_file = file_name
        check_function_type(func)
        return func
    return g

def URL_RULE(rule):
    def g(func):
        func.url_rule = rule
        check_function_type(func)
        return func
    return g


def UOM_WRAPS(func):
    def swraps(wraps):
        functools_wraps = functools.wraps(func)
        wraps = functools_wraps(wraps)
        wraps.uom_wraps_args = inspect.getargspec(func)
        return wraps
    return swraps

def get_arginfo(arg, arg_dict):
    arg_info = str(arg_dict[arg])
    arg_info = arg_info.replace('<', '[')
    arg_info = arg_info.replace('>', ']')
    return arg_info

class Rule:
    def __init__(self, context, module, cls, method, arg_info, clsobj):
        self._module = (module.__name__, module)
        self._cls = (cls.__name__, cls)
        self._method = (method.__name__, method)
        self._args = arg_info[0]
        self._arg_dict = arg_info[1]
        self._arg_keywords = arg_info[2]
        self._clsobj = clsobj
        self._url_mod = None
        if hasattr(method, 'post'):
            self._post = method.post
        else:
            self._post = False
        if hasattr(method, 'post_file'):
            self._post_file = method.post_file
        else:
            self._post_file = None

    def __repr__(self):
        return '<%s rule:%s module:%s class:%s method:%s args:%s argdict:%s>' %(
            self.__class__, self.rule(), self._module[0],
            self._cls[0], self._method[0],
            self._args, self._arg_dict)

    def set_url_mod(self, mod):
        self._url_mod = mod

    def get_url_mod(self):
        return self._url_mod

    def get_args(self):
        return self._args

    def get_arg_dict(self):
        return self._arg_dict

    def get_arg_keywords(self):
        return self._arg_keywords

    def setup_error_handler(self, handler, clsobj):
        if hasattr(clsobj, '_error_handle__404'):
            handler._error_obj__404 = clsobj        
        
        if hasattr(clsobj, '_error_handle__500'):
            handler._error_obj__500 = clsobj

        if hasattr(clsobj, '_error_handle__missing_parameter'):
            handler._error_obj__missing_parameter = clsobj

        if hasattr(clsobj, '_error_handle__parameter_type_failed'):
            handler._error_obj__parameter_type_failed = clsobj
        
        if hasattr(clsobj, '_error_handle__html_error'):
            handler._error_obj__html_render_error = clsobj

        if hasattr(clsobj, '_error_handle__process_error'):
            handler._error_obj__process_error = clsobj

    def get_handler(self):
        # tornado handler
        import SpuRequest
        class handler(SpuRequest.SpuBaseHandler):
            pass
        clsobj = self._clsobj
        cobj_class = self._cls[1]
        method = self._method[1]
        rule = self
        if not clsobj:
            clsobj = cobj_class()
        self.setup_error_handler(handler, clsobj)
        # call from processer
        def caller(self, **kwargs):
            _clsobj = clsobj
            _clsobj._set_tornado(self)
            _clsobj._set_rule(rule)
            if hasattr(self, 'session'):
                _clsobj._set_session(self.session)
            r = None
            # SpuDebug performance replace method
            if hasattr(method, 'replace_method'):
                r = method.__call__(_clsobj, **kwargs)
            else:
                r = method(_clsobj, **kwargs)
            if hasattr(self, 'session'):
                self.session = _clsobj._get_session()
        handler.processer_obj = clsobj
        handler.processer = caller
        handler.rule = rule
        return handler

    def _rule_module(self):
        raise NotImplInterface(self.__class__, '_rule_module')

    def _rule(self):
        raise NotImplInterface(self.__class__, '_rule')

    def _arg_rule(self):
        raise NotImplInterface(self.__class__, '_arg_rule')

    def rule_module(self):
        return self._rule_module()

    def rule(self):
        return self._rule()

    def rule_doc(self, c = '\n', t = '\t'):
        # interface url
        u = "*接口路径:* " + self._rule_module()
        post = ''
        if not self._post:
            u = u + self._arg_rule(c)
        else:
            u += c
            args = ['*post参数:*<br>']
            for arg in self._args:
                if arg == self._post_file:
                    arg = "*文件参数:" + arg + "*"
                arg_info = get_arginfo(arg, self._arg_dict)
                args.append("%s arginfo: %s" % (arg, arg_info))
                args.append('<br>')
            if len(args):
                args.pop()
            u = u + ''.join(args) + c
            post = '[post]'
            
        if self._arg_keywords:
            u += '*允许可变参数(**%s)' % self._arg_keywords + c

        # rule
        u += "*URL规则:* " + self._rule() + c
        # doc
        doc = self._method[1]
        if doc.__doc__:
            u += post + "*接口说明:*" + c + t + doc.__doc__
        u += c + c
        u = re.sub('\n', c, u)
        return (u,
                self._module[0],
                self._cls[0],
                self._method[0])

class Rule_path_and_argument(Rule):
    """/module/class/method/args_name=value&args_name=value&args_name=value"""
    def __init__(self, context, module, cls, method, arg_info, clsobj):
        Rule.__init__(self, context, module, cls, method, arg_info, clsobj)
        self.set_url_mod(url_rule__path_and_argument)

    @classmethod
    def rule_module_s(self, module, cls, method):
        return "/%s/%s/%s" % (module, cls, method)

    @classmethod
    def arg_rule_s(self, args_r, arg_dict):
        args = ['/']
        for arg in args_r:
            if type(arg) == tuple:
                key = arg[0]
                value = arg[1]
            else:
                key = arg
                value = get_arginfo(arg, arg_dict)
            if not value:
                continue
            args.append(key)
            args.append('=%s' % value)
            args.append('&')
        if len(args):
            args.pop()
        return ''.join(args)

    def _rule_module(self):
        return self.rule_module_s(self._module[0],
                                  self._cls[0],
                                  self._method[0])

    def _rule(self):
        s = self._rule_module()
        if not self._post and len(self._args):
            return s + "/?(/.+?)?"
        return s

    def _arg_rule(self, c):
        return self.arg_rule_s(self._args, self._arg_dict) + c

class Rule_path_file_and_argument(Rule):
    """/module/class/method?args_name=value&args_name=value&args_name=value"""
    def __init__(self, context, module, cls, method, arg_info, clsobj):
        Rule.__init__(self, context, module, cls, method, arg_info, clsobj)
        self.set_url_mod(url_rule__path_file_and_argument)

    @classmethod
    def rule_module_s(self, module, cls, method):
        return "/%s/%s/%s" % (module, cls, method)

    @classmethod
    def arg_rule_s(self, args_r, arg_dict):
        args = ['?']
        for arg in args_r:
            if type(arg) == tuple:
                key = arg[0]
                value = arg[1]
            else:
                key = arg
                value = 'value'
            if not value:
                continue
            args.append(key)
            args.append('=%s' % get_arginfo(arg, arg_dict))
            args.append('&')
        if len(args):
            args.pop()
        return ''.join(args)

    def _rule_module(self):
        return self.rule_module_s(self._module[0],
                                  self._cls[0],
                                  self._method[0])

    def _rule(self):
        s = self._rule_module()
        return s

    def _arg_rule(self, c):
        return self.arg_rule_s(self._args, self._arg_dict) + c

class Rule_path_and_value(Rule):
    """/module/class-method-value-value-value-value"""
    def __init__(self, context, module, cls, method, arg_info, clsobj):
        Rule.__init__(self, context, module, cls, method, arg_info, clsobj)
        self.set_url_mod(url_rule__path_and_value)

    @classmethod
    def rule_module_s(self, module, cls, method):
        return "/%s/%s-%s" % (module, cls, method)

    @classmethod
    def arg_rule_s(self, args_rt, arg_dict):
        args = []
        for arg in args_rt:
            if type(arg) == tuple:
                value = arg[1]
            else:
                value = arg
            if not value:
                value = ''
            args.append('-%s' % get_arginfo(arg, arg_dict))
        return ''.join(args)

    def _rule_module(self):
        return self.rule_module_s(self._module[0],
                                  self._cls[0],
                                  self._method[0])

    def _rule(self):
        s = self._rule_module()
        if not self._post and len(self._args):
            return s + "-(.+?)"
        return s

    def _arg_rule(self, c):
        return self.arg_rule_s(self._args, self._arg_dict) + c

class SpuUOM:

    _logging = SpuLogging(module_name = 'SpuUOM',
                          class_name = 'SpuUOM',
                          app_log=False)
    
    modules = []
    rule_list = []
    uom_map = {}
    context = None
    debug = False

    @classmethod
    def set_debug(cls, debug):
        cls.debug = debug

    @classmethod
    def load_spusys(cls):
        import SpuSys
        cls.add_module((SpuSys, url_rule__path_and_argument))

    @classmethod
    def import_module(cls, module, mtype=url_rule__path_and_argument):
        module = __import__(module)
        cls.add_module((module, mtype))

    @classmethod
    def add_module(cls, module):
        cls.modules.append(module)

    @classmethod
    def get_class_list(cls, m):
        from SpuRequest import SpuRequestHandler
        class_list = []
        class_strlist = dir(m)
        for c in class_strlist:
            obj = m.__dict__[c]
            # remove import symbol
            if inspect.getmodule(obj) == m and \
                   inspect.isclass(obj) and \
                   (issubclass(obj, SpuRequestHandler) or 
                    issubclass(obj, tornado.web.UIModule)):
                class_list.append(obj)
        return class_list

    @classmethod
    def get_method_list(cls, c):
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

    @classmethod
    def get_arg_info(cls, method):
        """return (args_list, args_dict, keywords)
        args_list: [arg_name1, arg_name2,...]
        args_dict: {arg_name1:{}, arg_name2:None}
        keywords: None or str(keywords name)
        """
        if hasattr(method, 'uom_wraps_args'):
            args = method.uom_wraps_args
        else:
            args = inspect.getargspec(method)

        try:
            args.args.remove('self')
        except Exception:
            raise Exception('%s no self arg' % method)
        args_list = args.args
        defaults = args.defaults
        args_dict = {}
        args_len = len(args_list)
        def_len = 0
        if defaults:
            def_len = len(defaults)
        s = args_len - def_len
        for idx in xrange(args_len):
            info = None
            if idx >= s:
                info = defaults[idx-s]
            args_dict[args_list[idx]] = info
        return (args_list, args_dict, args.keywords)

    @classmethod
    def uom_key(cls, _module, _class, _method):
        if hasattr(_module, '__name__'):
            _module = _module.__name__
        if hasattr(_class, '__name__'):
            _class = _class.__name__
        if hasattr(_method, '__name__'):
            _method = _method.__name__
        return '_'.join([_module, _class, _method])

    @classmethod
    def load(cls):
        for module in cls.modules:
            cls._logging.spu_debug('* Load Module: %s' % str(module))
            rule_type = module[1]
            module = module[0]
            classlist = cls.get_class_list(module)
            for c in classlist:
                cls._logging.spu_debug('|\t-> Load Class: %s' % str(c))
                if c.__dict__.get('new_instance', None):
                    clsobj = None
                else:
                    clsobj = c()
                methodlist = cls.get_method_list(c)
                for method in methodlist:
                    rt = rule_type
                    if hasattr(method, 'url_rule'):
                        rt = method.url_rule
                    cls._logging.spu_debug('|\t\t-> Load Method: %s UrlRule: %s' % (str(method), rt))
                    arg_info = cls.get_arg_info(method)
                    r_cls = create_rule(rt)
                    rule = r_cls(cls.context, module, c, method, arg_info, clsobj)
                    cls.rule_list.append(rule)
                    cls.uom_map[cls.uom_key(module, c, method)] = rule

    @classmethod
    def get_uom_map(cls):
        return cls.uom_map

    @classmethod
    def get_rule_by_source_info(cls, module, _class, method):
        return cls.uom_map.get(cls.uom_key(module, _class, method), None)

    @classmethod
    def url_rule_list(cls, doc = True):
        """
        return: [(url_rule_reg, handler)]
        """
        l = []
        for rule in cls.rule_list:
            r = (rule.rule(), rule.get_handler())
            l.append(r)
        # add doc handler
        if doc:
            r = ('/docs', DocHandler)
            l.append(r)
        return l

    @classmethod
    def rule_doc_list(cls, c = '\n', t = '\t'):
        doc_api_total = 0
        module_total = {}
        cls_total = {}
        docs = []
        for rule in cls.rule_list:
            (r, module, cls, method) = rule.rule_doc(c, t)
            docs.append(r)
            # total
            doc_api_total += 1
            if not module_total.get(module, None):
                module_total[module] = 1
            else:
                module_total[module] += 1
            if not cls_total.get(cls, None):
                cls_total[cls] = 1
            else:
                cls_total[cls] += 1

        doc_info = "Api Total:%s%s" % (doc_api_total, c*2)
        doc_info += "Module Total:%s%s" % (len(module_total.keys()), c)
        for k in module_total:
            doc_info += " [%s] Api Count:%s%s" % (k, module_total[k], c)
        doc_info += "%s" % c*2            
        doc_info += "Class Total:%s%s" % (len(cls_total.keys()), c)
        for k in cls_total:
            doc_info += " [%s] Api Count:%s%s" % (k, cls_total[k], c)
        doc_info += "%s" % c*2
        return doc_info + ''.join(docs)

DOC = []
def setdoc(doc):
    global DOC
    DOC.append(doc)

class DocHandler(tornado.web.RequestHandler):
    def get(self):
        l = '<br>'
        docs = SpuUOM.rule_doc_list(l)
        docs += l.join(DOC)
        self.write(docs)

class SpuUrlGenerator:
    """
    rule_type default is None
    """
    def __init__(self, rule_type = None):
        self._rule_type = rule_type
        self.reset()

    def reset(self):
        self._state = 0
        self._module = None
        self._class = None
        self._method = None
        self._args = {}
        self._rule = None

    def __getattr__(self, name):
        if self._state == 0:
            self._module = name
        elif self._state == 1:
            self._class = name
        elif self._state == 2:
            self._method = name
        else:
            assert None, "Url Generator State Faield: state(%s) name(%s)" % (self._state, name)
        self._state += 1
        return self

    def _get_rule(self):
        if self._rule_type:
            self._rule = create_rule(self._rule_type)
        else:
            rule = SpuUOM.get_rule_by_source_info(self._module,
                                                  self._class,
                                                  self._method)
            self._rule = rule

    def _get_path(self):
        path = self._rule.rule_module_s(self._module,
                                  self._class,
                                  self._method)
        return path

    def _get_define_arg(self, args, kwargs):
        args_info = self._rule.get_args()
        for arg in args_info:
            value = kwargs.get(arg, None)
            t = (arg, value)
            args.append(t)
            if kwargs.has_key(arg):
                del kwargs[arg]

    def _get_query(self, kwargs):
        args = []
        if not self._rule_type:
            # use arg define in rule
            self._get_define_arg(args, kwargs)
        for arg in kwargs:
            t = (arg, kwargs[arg])
            args.append(t)
        query = self._rule.arg_rule_s(args)
        return query

    def __call__(self, **kwargs):
        self._get_rule()
        path = self._get_path()
        query = self._get_query(kwargs)
        url = path + query
        self.reset()
        return url

