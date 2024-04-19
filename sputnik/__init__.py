#-*- coding: utf-8 -*
#
# Copyright 2011, 2012, 2013, 2014 mibang
# by error.d@gmail.com
# 2014-08-01
#

from tornado import version_info
from tornado import autoreload

if version_info[0] == 4:
    from tornado.log import enable_pretty_logging
else:
    from tornado.options import enable_pretty_logging

from SpuLogging import SpuLogging

G_INIT = False
G_DEBUG = None

version = '0.5.5'

default_assert_config = {
 'model_field_define_assert' : True
}

global_assert_config = None

def _autoreload_remove_db_connect():
    from SpuContext import SpuContext
    spudb = SpuContext.get_g_spudb()
    if spudb:
        SpuLogging.info("autoreload close last db connect %s" % spudb)
        spudb.close()

def is_debug():
    return G_DEBUG

def sputnik_init(_logging_config,
                 debug=False,
                 cache_config=None,
                 spusys_config=None,
                 assert_config=default_assert_config):
    """
    Sputnik Init
    """

    global G_DEBUG
    global G_INIT

    if G_INIT:
        return
    G_INIT = True
    G_DEBUG = debug
    SpuLogging.setting(_logging_config)
    autoreload.add_reload_hook(_autoreload_remove_db_connect)

    global global_assert_config
    global_assert_config = assert_config

    enable_pretty_logging()
    
    if cache_config:
        from SpuCacheManager import SpuCacheManager
        SpuCacheManager.setting(cache_config, debug)


    if spusys_config:
        import SpuSys
        SpuSys.setting(spusys_config, debug)

