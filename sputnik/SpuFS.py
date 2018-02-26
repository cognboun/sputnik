#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-11-3
#
# Sputnik File System (IFS)
#
# ToDoList:
# 

import random
import os
from SpuDateTime import SpuDateTime
from SpuDebug import *
from SpuLogging import *

_fs = {}

def createSpuFS(type, cfg, fs_name = 'fs_default'):
    global _fs
    if not type or type == 'spuFS' or type == 'default':
        _fs[fs_name] = SpuFileSystem(cfg)
        return
    assert None, 'Unknow SpuFileSystem Type:%s' % type

def getSpuFS(fs_name = 'fs_default'):
    global _fs
    if _fs:
        if fs_name not in _fs:
            assert None, 'Not File System Name: %s' % fs_name
            pass
        return _fs[fs_name]
    assert None, 'Not Create SpuFS'

class SpuFileSystem:
    def __init__(self, cfg):
        self._cfg = cfg
        self.root_dir = cfg.get('root', None)
        self.urlbase = cfg.get('urlbase', None)
        self._debug_time = SpuDebugTime()
        self._logging = SpuLogging()
        self._logging.set_class('SpuFileSystem')
        assert self.root_dir, 'Not Root Path'
        assert self.urlbase, 'Not Url Base'

    def mkdir(self, dir_path):
        full_path = self.full_path(dir_path, '')
        os.makedirs(full_path)

    def rmdir(self, dir_path):
        full_path = self.full_path(dir_path, '')
        os.removedirs(full_path)

    def isfile(self, path, file):
        full_path = self.full_path(path, file)
        return os.path.isfile(full_path)

    def exists(self, path):
        full_path = self.full_path(path, '')
        return os.path.exists(full_path)

    def _new_file(self, dir_path, file_name, open_type, file):
        full_path = self.full_path(dir_path, file_name)
        try:
            fd = open(full_path, open_type)
            fd.write(file)
            fd.close()
        except IOError as m:
            if m.errno == 2:
                return False
        return True

    def new_binfile(self, dir_path, file_name, file):
        self._logging.set_function('new_binfile')
        self._debug_time.start()
        b = self._new_file(dir_path, file_name, 'wb', file)
        t = self._debug_time.end()
        self._logging.perf("file:%s" % dir_path + file_name, t)
        return b

    def get_file_size(self, dir_path, file_name):
        full_path = self.full_path(dir_path, file_name)
        return os.path.getsize(full_path)

    def read_binfile(self, dir_path, file_name):
        self._logging.set_function('read_binfile')
        self._debug_time.start()
        full_path = self.full_path(dir_path, file_name)
        try:
            fd = open(full_path, 'rb')
            file_size = self.get_file_size(dir_path, file_name)
            binfile = fd.read(file_size)
            fd.close()
        except Exception as m:
            self._logging.error('read_binfile error: %s' % m)
            binfile = None
        t = self._debug_time.end()
        self._logging.perf("file:%s" % dir_path + file_name, t)
        return binfile

    def new_textfile(self, dir_path, file_name, file):
        return self._new_file(dir_path, file_name, 'w', file)

    def remove_file(self, dir_path, file_name):
        full_path = self.full_path(dir_path, file_name)
        os.remove(full_path)

    def _merge_path(self, a, b):
        if a[-1] == '/' and b[0] == '/':
            c = a + b[1:]
        elif a[-1] != '/' and b[0] != '/':
            c = ''.join([a, '/', b])
        else:
            c = a + b
        return c

    def full_path(self, dir_path, file_name):
        full_path = self._merge_path(self.root_dir, dir_path)
        if file_name:
            full_path = self._merge_path(full_path, file_name)
        return full_path

    def url(self, dir_path, file_name):
        url = self._merge_path(self.urlbase, dir_path)
        if file_name:
            url = self._merge_path(url, file_name)
        return url

def make_timebase_path(base):
    (y, m, d) = SpuDateTime.y_m_d()
    return "%s/%s/%s/%s/" % (base, y, m, d)

def make_random_arg_path(suffix, *args):
    l = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
         'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
         'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 
         'y', 'z']
    fl = []
    if len(args) > 1:
        for arg in args:
            if type(arg) == float:
                arg = int(arg)
            fl.append(str(arg))
            fl.append(random.choice(l))
        sfilename = ''.join(fl)
    else:
        sfilename = str(args[0])
    filename = sfilename + '%s' % suffix
    return (sfilename, filename)

if __name__ == "__main__":
    createSpuFS(None, {'root':'.', 'urlbase':'http://www.google.com'})
    fs = getSpuFS()
    p = '/aa/bb/cc'
    fn = 'asf'
    fs.mkdir(p)
    if not fs.exists(p):
        assert None, 'mkdir faield %s' % p
    fs.new_textfile(p, fn, 'aaaaa')
    full = fs.full_path(p, fn)
    fs.remove_file(p, fn)
    if fs.exists(full):
        assert None, 'rm file faield'
    fs.rmdir(p)
    if fs.exists(p):
        assert None, 'rm dir faield'
    print fs.url(p, fn)
    print 'success'
