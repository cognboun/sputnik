#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-17
#
# Sputnik Url
#
# ToDoList:
# 

from SpuException import NotImplInterface

"""/module/class/method/args_name=value&args_name=value&args_name=value"""
url_rule__path_and_argument = 1

"""/module/class/method?args_name=value&args_name=value&args_name=value"""
url_rule__path_file_and_argument = 2

"""/module/class-method-value-value-value-value"""
url_rule__path_and_value = 3

def create_url(type):
    if (type == url_rule__path_and_argument or 
        type == url_rule__path_file_and_argument):
        return SpuUrlArgumentPattern
    elif type == url_rule__path_and_value:
        return SpuUrlValuePattern
    assert None, 'Unknow Url Type'

def format_arg(url_arg):
    if url_arg[0:7] == "format=":
        return url_arg[7:]
    return None

class SpuUrl:
    def __init__(self, url = None):
        self._url = url
    
    def __str__(self):
        if not self._url:
            self.generation_url()
        return self._url

    def _parse(self):
        raise NotImplInterface(self.__class__, '_parse')
    
    def _generation_url(self):
        raise NotImplInterface(self.__class__, '_generation_url')

    def get_url(self):
        return str(self)

    def get_real_url(self):
        self._url = None
        return str(self)

    def parse(self):
        if not self._url:
            return False
        return self._parse()

    def generation_url(self):
        return self._generation_url()

class SpuUrlPathPattern(SpuUrl):
    """
    Url Pattern: yy/yy/yy/yy
    """
    def __init__(self, url = None):
        SpuUrl.__init__(self, url)
        self._list = []

    def _parse(self):
        l = self._url.split('/')
        self._list = []
        for i in l:
            if i and len(i.strip()) > 0:
                self._list.append(i)
        return True

    def _generation_url(self):
        self._url = '/'.join(self._list)

    def __add__(self, path):
        self.append_path(path)
        return self

    def __getitem__(self, index):
        return self._list[index]

    def append_path(self, path):
        self._list.append(path)

class SpuUrlArgumentPattern(SpuUrl):
    """
    Url Pattern: xx=yy&xx=yy&xx=yy&xx=yy
    """
    def __init__(self, url = None):
        SpuUrl.__init__(self, url)
        self._dict = {}

    def _parse(self):
        if self._url[0] == '/':
            self._url = self._url[1:]
        kvs = self._url.split('&')
        for kv in kvs:
            if not kv.strip():
                continue
            t = kv.split('=')
            k = str(t[0])
            if len(t) == 2:
                v = t[1]
                # xx=&yy=1, xx is None, yy is 1
                if not v: # v is ''
                    v = None
                self._dict[k] = v
            else:
                # xx&yy=1, xx is None, yy is 1
                self._dict[k] = None
    
    def _generation_url(self):
        url = []
        for key in self._dict.keys():
            url.append(key)
            if self._dict[key] != None:
                url.append('=')
                url.append(self._dict[key])
                url.append('&')
        if len(url) > 0 and url[-1] == '&':
            url.pop()
        self._url = ''.join(url)

    def get(self, key, default = None):
        return self._dict.get(key, default)

    def set(self, key, value = None):
        self._dict[key] = value

    def del_key(self, key):
        del self._dict[key]

    def dict(self):
        return self._dict

    def keys(self):
        return self._dict.keys()

    def has_key(self, key):
        return self._dict.has_key(key)

class SpuUrlValuePattern(SpuUrl):
    """
    Url Pattern: value-value-value-value
    """
    def __init__(self, url = None):
        SpuUrl.__init__(self, url)
        self._value = []
        self._arg_list = None
        self._dict = {}

    def _parse(self):
        if self._url[0] == '/':
            self._url = self._url[1:]
        values = self._url.split('-')
        idx = 0
        for value in values:
            value = value.strip()
            format = format_arg(value)
            if format:
                self._dict['format'] = format
            self._value.append(value)
            # add dict
            if self._arg_list:
                if idx+1 > len(self._arg_list):
                    continue
                arg_name = self._arg_list[idx]
                self._dict[arg_name] = value
                idx += 1

    def _generation_url(self):
        return '-'.join(self._value)

    def __getitem__(self, index):
        if self._value:
            return self._value[index]
        return None

    def set_arg_list(self, arg_list):
        self._arg_list = arg_list

    def get(self, key, default = None):
        return self._dict.get(key, default)

    def set(self, key, value = None):
        self._dict[key] = value

    def del_key(self, key):
        del self._dict[key]

    def dict(self):
        return self._dict

    def keys(self):
        return self._dict.keys()

    def has_key(self, key):
        return self._dict.has_key(key)

class SpuUrlPathAndArgumentPattern(SpuUrl):
    """
    Url Pattern: yy/yy/yy/xx=yy&xx=yy&xx=yy&xx=yy
    """
    def __init__(self, url = None):
        SpuUrl.__init__(self, url)
        self._path = None
        self._args = None

    def _is_args(self, args):
        if args.find('=') == -1 and args.find('&') == -1:
            return False
        return True

    def _parse(self):
        p = self._url.rfind('/')
        path = ''
        args = ''
        if p == -1:
            if self._is_args(self._url):
                args = self._url
            else:
                path = self._url
        else:
            p += 1
            path = self._url[:p]
            args = self._url[p:]
            if not self._is_args(args):
                path += args
                args = ''
        self._path = SpuUrlPathPattern(path)
        self._path.parse()
        self._args = SpuUrlArgumentPattern(args)
        self._args.parse()
        return True
    
    def _generation_url(self):
        if self._path:
            self._url = self._path.get_url()
        if self._args:
            if self._url:
                self._url += '/'
            else:
                self._url = ''
            self._url += self._args.get_url()        

    def __add__(self, path):
        self.append_path(path)
        return self

    def __getitem__(self, index):
        if self._path:
            return self._path[index]
        return None
    
    def append_path(self, path):
        if not self._path:
            self._path = SpuUrlPathPattern()
        self._path.append_path(path)

    def set(self, key, value = None):
        if not self._args:
            self._args = SpuUrlArgumentPattern()
        self._args.set(key, value)

    def get(self, key):
        if self._args:
            return self._args.get(key)
        return None

    def del_key(self, key):
        if self._args:
            self._args.del_key()

    def keys(self):
        if self._args:
            return self._args.keys()
        return None

    def has_key(self, key):
        if self._args:
            return self._args.has_key(key)
        return False

class SpuUrlPathAndValuePattern(SpuUrl):
    """
    Url Pattern: yy/yy/yy/value-value-value-value
    """
    def __init__(self, url = None):
        SpuUrl.__init__(self, url)
        self._path = None
        self._args = None
