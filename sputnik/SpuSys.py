#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 msx.com
# Copyright 2013 msx.com
# Copyright 2014 lrzm.com
# by error.d@gmail.com
# 2014-12-23
#
# Sputnik System Info
#

import os
import json
import time
import base64
import thread
import requests
import tornado
import tornado.httpserver
import SpuUOM
from SpuLogging import SpuLogging
from SpuRequest import SpuRequestHandler
from SpuPythonObject import Pyobject, PyobjectList
from SpuUtil import get_local_ip

# monitor module
import sputnik
from SpuCacheManager import SpuCacheManager

# logging
_logging = SpuLogging('SpuSystem')

# state
success = (200, 'success')
cache_type_error = (201, 'error cache type')
action_error = (202, 'error action')

class alive(SpuRequestHandler):

    def ping(self):
        tid = thread.get_ident()
        return self._response(Pyobject(success, {'status' : 'ok',
                                                 'tid' : tid}))

class sysinfo(SpuRequestHandler):
    start_time = time.time()

    def __version(self):
        version_info = {
            'tornado' : tornado.version,
            'sputnik' : sputnik.version,
            }
        return version_info

    def __process_start_time(self):
        ts = time.localtime(self.start_time)
        ts = time.strftime("%Y-%m-%d %H:%M:%S", ts)
        return ts

    def __process_run_time(self):
        return time.time() - self.start_time

    def version(self):
        return self._response(Pyobject(success, self.__version()))

    def process_start_time(self):
        return self._response(Pyobject(success, self.__process_start_time()))

    def process_run_time(self):
        return self._response(Pyobject(success, self.__process_run_time()))

    def all(self):
        result = {
            'version' : self.__version(),
            'process_start_time' : self.__process_start_time(),
            'process_run_time' : self.__process_run_time()
            }
        return self._response(Pyobject(success, result))

class tornado_sys(SpuRequestHandler):

    def __get_ioloop_info(self):
        ioloop = tornado.ioloop.IOLoop.instance()
        io_handler = ioloop._handlers

        ioloop_info = []
        for fd, handler in io_handler.items():
            ioloop_info.append('%s:%s' % (fd, handler.func))
        return ioloop_info

    def ioloop_info(self):
        """
        get ioloop info
        """
        ioloop_info = self.__get_ioloop_info()
        return self._response(Pyobject(success, {'status' : 'ok',
                                                 'socket_count' : len(ioloop_info),
                                                 'ioloop_info' : ioloop_info}))

class cache(SpuRequestHandler):

    def cache_info(self):
        """
        get all cache info
        """
        cache_info = {}
	for cache_obj, cache_name, cache_type in SpuCacheManager._c_cache:
            _cache = {}
            if cache_obj:
                access = cache_obj.access() + 2
                hit = cache_obj.hit() + 1
                miss = cache_obj.miss() + 1
                hit_rate = '%s%%' % round(float(hit) / float(access) * 100, 2)
                miss_rate = '%s%%' % round(float(miss) / float(access) * 100, 2) 
                _cache['enable']  = True
                _cache['cache_size'] = cache_obj.cache_size()
                _cache['access'] = access
                _cache['hit'] = hit
                _cache['miss'] = miss
                _cache['hit_rate'] = hit_rate
                _cache['miss_rate'] = miss_rate
            else:
                _cache['enable'] = False
            cache_info[cache_name] = _cache
        result = {'cache_info' : cache_info}
        return self._response(Pyobject(success, result))

    def __process_get(self, action, values):
        if action == 'get_all':
            for key, value in values.items():
                try:
                    json.dumps(value)
                except Exception:
                    values[key] = base64.b64encode(value)
            return values

        if action == 'get_value':
            try:
                json.dumps(values)
            except Exception:
                return base64.b64encode(values)
        return values

    def process_cache_original_keys(self,
                                    key_rule={'atype': str, 'aneed': True}):
        """
        """
	for cache_obj, _, cache_type in SpuCacheManager._c_cache:
            if cache_obj and cache_type == SpuCacheManager.ProcessCache:
                result = cache_obj.original_keys(key_rule)
                return self._response(PyobjectList(success, result))        
        return self._response(Pyobject(cache_type_error, None))

    def cache_action(self,
                     cache_type={'atype': str, 'aneed': True},
                     action={'atype': str, 'aneed': True},
                     **kwargs):
        """
        run cache action
        action list:
          set_value(self, key, value, expire=0)
          get_value(self, key)
          remove(self, key)
          keys(self, key_rule)
          cache_size(self)
          get_all(self)
          expire(self, key, expire_time)
          ttl(self, key)
        """
        result = None
        if 'expire' in kwargs:
            kwargs['expire'] = int(kwargs['expire'])
        if 'expire_time' in kwargs:
            kwargs['expire_time'] = int(kwargs['expire_time'])
	for cache_obj, cache_name, _ in SpuCacheManager._c_cache:
            if cache_obj and cache_name == cache_type:
                if hasattr(cache_obj, action):
                    result = getattr(cache_obj, action)(**kwargs)
                    result = self.__process_get(action, result)
                    return self._response(PyobjectList(success, result))
                else:
                    return self._response(Pyobject(action_error, None))
        return self._response(Pyobject(cache_type_error, None))

def register_sputnik_process(spumaster_server_addr, app_port, network_interface):
    _logging.spu_info('Register sputnik process...')
    # eth0
    ip = get_local_ip(network_interface)
    pid = os.getpid()
    try:
        req = requests.get('http://%s/register_sputnik_process/' \
                           'ip=%s&port=%s&pid=%s' % (spumaster_server_addr,
                                                     ip, app_port, pid))
    except Exception as m:
        _logging.info('Register sputnik exception %s', m)
        return
    if req.ok and req.text == 'ok':
        status = 'success'
    else:
        status = 'failed'
    _logging.info('Register sputnik process %s', status)

# api

def start_spusys_on_main_http_server(spumaster_server_addr, app_port,
                                     network_interface):
    _logging.info('Start spusys main http server...')
    SpuUOM.SpuUOM.load_spusys()
    register_sputnik_process(spumaster_server_addr, app_port,
                             network_interface)

def start_spusys_on_http_server_thread(spumaster_server_addr, app_port,
                                       network_interface):
    class Application(tornado.web.Application):
        def __init__(self):
            handlers = SpuUOM.SpuUOM.url_rule_list(True)

            settings = dict(
                debug = True,
                service_title=u'SpuSys Http Server'
                )
            tornado.web.Application.__init__(self, handlers, **settings)

    def spusys_http_server_thread():
        SpuUOM.SpuUOM.load_spusys()
        SpuUOM.SpuUOM.load()
        # use new ioloop
        ioloop = tornado.ioloop.IOLoop()
        http_server = tornado.httpserver.HTTPServer(Application(),
                                                    xheaders=True,
                                                    io_loop=ioloop)
        _logging.info('Start SpuSys http server thread:%s port:%s ...',
                      thread.get_ident(),
                      app_port)
        http_server.listen(app_port)
        ioloop.start()
        
    thread.start_new_thread(spusys_http_server_thread, ())
    register_sputnik_process(spumaster_server_addr, app_port, network_interface)

def setting(conf, debug):
    if not conf.get('enable', False):
        return

    spumaster_server_addr = conf['spumaster_server_addr']
    app_port = conf['app_port']
    network_interface = conf.get('network_interface', 'eth0')

    if conf.get('http_thread', False):
        start_spusys_on_http_server_thread(spumaster_server_addr, app_port,
                                           network_interface)
    else:
        start_spusys_on_main_http_server(spumaster_server_addr, app_port,
                                         network_interface)

