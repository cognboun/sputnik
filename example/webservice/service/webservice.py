#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 2013 2014 msx.com
# by error.d@gmail.com
# 2014-08-26
#

"""

"""

import sys
import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web

def init_cache():
    cache_config = {
        'process' : {
        'enable' : True,
        'type' : 'process',
        'policy': 'lru',
        },
        'local' : {
        'enable' : True,
        'type' : 'remote',
        'db': 6,
        'host': '127.0.0.1',
        'port': 6380
        },
        'global' : {
        'enable' : False,
        'type' : 'remote',
        'db': 6,
        'host': '10.132.62.119',
        'port': 6380
        },

        'cache_monitor' : {
        'enable' : True,
        'mq_addr' : 'tcp://127.0.0.1:5555',
        'pub_addr' : 'tcp://127.0.0.1:2222',
        'remove_cache_type' : ['ProcessCache']
        }
        }
    SpuCacheManager.setting(cache_config, DEBUG)

def init():

    start_sputnik_logging(error_log_path='./error.log')
    init_cache()
    db = SpuDBCreateDB(dbcnf)
    dbc = db.create()
    dbc.set_charset('utf8mb4')
    dbc.connection()

    context = SpuContext(dbc, None, None)
    SpuContext.init_context(dbc, None)
    SpuDOFactory.init_factory(DEBUG, SpuCacheManager)
    SpuRequestHandler.set_context(context)

    import sputnik.SpuSys as spusys
    #spusys.start_spusys_on_http_server_thread('127.0.0.1:12345', app_port+10)
    #spusys.start_spusys_on_main_http_server('127.0.0.1:12345', app_port)
    SpuUOM.import_module('webservice_api')
    SpuUOM.load()

def start():
    class Application(tornado.web.Application):
        def __init__(self):
            if DEBUG:
                doc = True
            else:
                doc = False
            handlers = SpuUOM.url_rule_list(doc)

            settings = dict(
                debug = DEBUG,
                service_title=u"Web Service"
                )
            tornado.web.Application.__init__(self, handlers, **settings)

    http_server = tornado.httpserver.HTTPServer(Application(), xheaders = True)
    SpuLogging.info("start success")
    http_server.listen(app_port)
    tornado.ioloop.IOLoop.instance().start()


def print_db_info():
    SpuLogging.info("DB Info:")
    SpuLogging.info("\tDB Type:%s" % dbcnf['dbtype'])
    SpuLogging.info("\tDB Host:%s" % dbcnf['host'])
    SpuLogging.info("\tDB Port:%s" % dbcnf['port'])
    SpuLogging.info("\tDB Database:%s" % dbcnf['database'])

def print_sys_info():
    SpuLogging.info("Web Service Version: %s" % '0.1')
    SpuLogging.info("Tornado Version: %s" % tornado.version)
    SpuLogging.info("Application Port:%s" % app_port)
    SpuLogging.info("Debug Mod:%s" % DEBUG)

def usage():
    print "usage: ./webservice.py [--option=value] configfile [--dev]"
    print "\t --dev\t\tno install Module"

def main():
    init()
    print_sys_info()
    print_db_info()
    #while True:pass
    start()

def calltrack_main():
    import webservice
    import sputnik
    
    cte = CallTrackerEngine(import_module=webservice)
    cte.calltrack_module(tornado.httpserver)
    cte.calltrack_module(tornado.ioloop)
    cte.calltrack_module(tornado.web)
    cte.calltrack_module(sputnik.SpuDBObject)
    cte.calltrack_module(sputnik.SpuUOM)
    cte.calltrack_module(sputnik.SpuRequest)
    cte.calltrack_module(sputnik.SpuCacheManager)
    main()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)
    
    from config import *
    main()
    #calltrack_main()

