#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 msx.com
# Copyright 2013 msx.com
# Copyright 2014 lrzm.com
# by error.d@gmail.com
# 2014-12-17
#
# Sputnik Cache Monitor
#

import thread
from SpuFastMQ import SpuFastMQProducer, SpuFastMQConsumer
from sputnik.SpuLogging import SpuLogging

_logging = SpuLogging(module_name='SpuCacheMonitor')

CACHE_MONITOR_TOPIC_KEY = 'CACHE_MONITOR'

class SpuCacheMMConsumer(SpuFastMQConsumer):
    import SpuCacheManager as cache_manager
    """ Sputnik Cache Monitor Message Consumer """

    def __init__(self, pub_addr, cache):
        super(SpuCacheMMConsumer, self).__init__(pub_addr,
                                                 CACHE_MONITOR_TOPIC_KEY)
        self._cache = cache

    def __call__(self, **kwargs):
        _logging.info('start cache monitor message consumer thread: %s',
                      thread.get_ident())
        self.pop_message_loop()

    # message handler -- remove_process_cache
    def remove_process_cache_handler(self, key):
        """ cache monitor message process handler """
        _logging.info('remove process cache key: %s' % key)
        self._cache.remove(key,
                           self.cache_manager.SpuCacheManager.ProcessCache,
                           cache_event=False)

    # message handler -- remove_local_cache
    def remove_local_cache_handler(self, key):
        """ cache monitor message local handler """

        _logging.info('remove local cache key: %s' % key)
        # cache_event is False
        self._cache.remove(key,
                           self.cache_manager.SpuCacheManager.LocalCache,
                           cache_event=False)

    # message handler -- remove_by_keyrule_process_cache
    def remove_by_keyrule_process_cache_handler(self, keyrule):
        """ cache monitor message process handler """ 

        _logging.info('remove by keyrule process cache keyrule:%s' % keyrule)
        self._cache.remove_by_keyrule(keyrule,
                                      self.cache_manager.SpuCacheManager.ProcessCache,
                                      cache_event=False)

    # message handler -- remove_by_keyrule_local_cache
    def remove_by_keyrule_local_cache_handler(self, keyrule):
        """ cache monitor message local handler """

        _logging.info('remove by keyrule local cache keyrule:%s' % keyrule)
        self._cache.remove_by_keyrule(keyrule,
                                      self.cache_manager.SpuCacheManager.LocalCache,
                                      cache_event=False)


    # message handler -- remove_all_process_cache
    def remove_all_process_cache_handler(self, arg):
        """ cache monitor message process handler """ 

        _logging.info('remove_all process cache')
        self._cache.remove_all(self.cache_manager.SpuCacheManager.ProcessCache,
                               cache_event=False)

    # message handler -- remove_all_local_cache
    def remove_all_local_cache_handler(self, arg):
        """ cache monitor message local handler """

        _logging.info('remove_all local cache')
        self._cache.remove_all(self.cache_manager.SpuCacheManager.LocalCache,
                               cache_event=False)

class SpuCacheMonitor(object):
    """
    Sputnik Cache Monitor
    """

    def __init__(self, mq_addr, cache_mm_consumer):
        """
        """
        self._mq_addr = mq_addr
        self._cache_mm_consumer = cache_mm_consumer
        self._cache_mq_producer = SpuFastMQProducer(self._mq_addr,
                                                    CACHE_MONITOR_TOPIC_KEY)
        self._monitor_thread = None

    def start_monitor_thread(self):
        """ start monitor thread """
        thread.start_new_thread(self._cache_mm_consumer, ())

    def remove_process_cache_event(self, key):
        """
        remove process cache event
        """
        self._cache_mq_producer.push_message('remove_process_cache',
                                            key) 

    def remove_local_cache_event(self, key):
        """
        remove local cache event
        """
        self._cache_mq_producer.push_message('remove_local_cache',
                                            key) 

    def remove_by_keyrule_process_cache_event(self, keyrule):
        """
        remove by key rule on process cache event
        """
        self._cache_mq_producer.push_message('remove_by_keyrule_process_cache',
                                             key) 

    def remove_by_keyrule_local_cache_event(self, keyrule):
        """
        remove by key rule on local cache event
        """
        self._cache_mq_producer.push_message('remove_by_keyrule_local_cache',
                                             key) 

    def remove_all_process_cache_event(self):
        """
        remove all on process cache event
        """
        self._cache_mq_producer.push_message('remove_all_process_cache',
                                             '')

    def remove_all_local_cache_event(self):
        """
        remove all on local cache event
        """
        self._cache_mq_producer.push_message('remove_all_local_cache',
                                             '') 
