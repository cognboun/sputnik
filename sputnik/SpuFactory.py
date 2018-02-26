#-*- coding: utf-8 -*
#
# Copyright 2012 msx.com
# by error.d@gmail.com
# 2012-4-9
#
# Factory Object
#
# 

import inspect
from SpuDB import SpuDBManager
from SpuBase import *
from SpuDBObject import *
from SpuLogging import SpuLogging

_logging = SpuLogging(module_name = 'SpuFactory')

class FactoryInfo:
    def __init__(self, spudb, spucache, debug):
        self._spudb = spudb
        self._spucache = spucache
        self._debug = debug

class SpuDOFactory:
    """ Sputnik Data Object Factory"""

    debug = None

    @classmethod
    def init_factory(cls, debug, cache=None):
        cls.debug = debug
        cls.cache = cache
        _logging.spu_debug('init_factory cache:%s' % bool(cache))

    @classmethod
    def set_cache(cls, cache):
        cls.cache = cache

    @classmethod
    def create_object(cls, object, module_object=None,
                      server=default_server, use_cache=True):
        """
        db server find order:
        1. create_object param server
        2. object define _dbserver_
        3. default_server
        """

        o = None
        args = inspect.getargspec(object.__init__).args
        if server == default_server and hasattr(object, '_dbserver_'):
            server = object._dbserver_
        spudb = SpuDBManager.get_spudb(server)
        spucache = cls.cache(use_cache) if cls.cache else None
        debug = cls.debug
        if len(args) == 4 or object is SpuDBObject or \
               issubclass(object, (SpuBase, SpuDBObject)):
            if 'base' in args:
                o = object(base = cls, spucache=spucache)
            else:
                o = object(spudb, spucache, debug)
        elif object is SpuDBObjectList or issubclass(object, SpuDBObjectList):
            #assert module_object and hasattr(module_object, '_table_') , \
            # "Create SpuDBObjectList Need Table Object"
            o = object(module_object, spudb,
                       spucache, debug)
        else:
            o = object()
        return o

def create_object(object, server=default_server, use_cache=True):
    """
    create data object
    """

    return SpuDOFactory.create_object(object, server=server, use_cache=use_cache)

def create_listobject(object, module_object,
                      server=default_server, use_cache=True):
    """
    create list data object
    """

    return SpuDOFactory.create_object(object, module_object, server=server,
                                      use_cache=use_cache)
