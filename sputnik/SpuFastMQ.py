#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 msx.com
# Copyright 2013 msx.com
# Copyright 2014 lrzm.com
# by error.d@gmail.com
# 2014-12-17
#
# Sputnik Fast Message Queue
#

"""
Fast Message Queue

message unsafe, no storage, but fast message queue
"""

import zmq
import cPickle
import thread
from sputnik.SpuLogging import SpuLogging

_logging = SpuLogging(module_name='SpuFastMQ')

class SpuFastMQServer(object):
    """
    Fast Message Queue Server
    """

    def __init__(self, pub_addr, mq_addr, io_threads=1):
        """
          pub_addr   - publish server bind address
          mq_addr    - message queue address
          io_threads - io threads number
        """
        self._pub_addr = pub_addr
        self._mq_addr = mq_addr
        self._io_threads = io_threads
        self._context = None
        self._pub_socket = None
        self._mq_socket = None
        self._init_server_context()

    def _init_server_context(self):
        """
        init fast message queue server context
        """
        self._context = zmq.Context(self._io_threads)
        # create message queue socket
        self._mq_socket = self._context.socket(zmq.PULL)
        self._mq_socket.bind(self._mq_addr)
        # create publish server socket
        self._pub_socket = self._context.socket(zmq.PUB)
        self._pub_socket.bind(self._pub_addr)

    def _pull_message(self):
        """ pull message from producer """
        msg = self._mq_socket.recv()
        return cPickle.loads(msg) if msg != 'exit' else msg

    def _publish_message(self, message):
        """ publish message to consumer """
        message[2] = cPickle.dumps(message[2])
        self._pub_socket.send_multipart(message)

    def message_dispatch(self):
        """
        message dispatch
        1. pull message from producer
        2. publish to consumer
        """

        _logging.info('start fast message queue')
        while True:
            msg = self._pull_message()
            _logging.info('recv message: %s', msg)
            if msg == 'exit':
                break
            self._publish_message(msg)
        _logging.info('end fast message queue')

class SpuFastMQProducer(object):
    """
    Fast Message Queue Producer
    message format:
     [topic_key, message_name, message_body]
    """

    def __init__(self, mq_addr, topic_key, io_threads=1):
        """
          mq_addr    - message queue address
          topic_key  - pub-sub topic key
          io_threads - io threads number
        """
        self._mq_addr = mq_addr
        self._topic_key = topic_key
        self._io_threads = io_threads
        self._context = None
        self._mq_socket = None
        self._init_producer_context()

    def _init_producer_context(self):
        """ init fast message queue producer context """
        self._context = zmq.Context(self._io_threads)
        self._mq_socket = self._context.socket(zmq.PUSH)
        self._mq_socket.connect(self._mq_addr)

    def stop_message_queue_server(self):
        """ stop message queue server """
        self._mq_socket.send('exit')

    def push_message(self, message_name, message_body):
        """ push message to mq """
        pickle_str = cPickle.dumps([self._topic_key, \
                                    message_name, message_body])
        return self._mq_socket.send(pickle_str)

class SpuFastMQConsumer(object):
    """
    Fast Message Queue Consumer
    """

    def __init__(self, pub_addr, topic_key, io_threads=1):
        """
        pub_addr   - publish server bind address
        topic_key  - pub-sub topic key, all topic set 'None'
        io_threads - io threads number
        """
        self._pub_addr = pub_addr
        self._io_threads = io_threads
        self._topic_key = topic_key
        self._context = None
        self._pub_socket = None
        self._init_consumer_context()

    def _init_consumer_context(self):
        """
        init fast message queue consumer context
        """
        self._context = zmq.Context(self._io_threads)
        self._pub_socket = self._context.socket(zmq.SUB)
        print 'a'*10, self._pub_addr
        self._pub_socket.connect(self._pub_addr)
        if not self._topic_key:
            _logging.debug('Receiving message on All topics')
            self._pub_socket.setsockopt(zmq.SUBSCRIBE, '')
        else:
            _logging.debug('Receiving message on topics: %s', self._topic_key)
            self._pub_socket.setsockopt(zmq.SUBSCRIBE, self._topic_key)

    def _is_exit(self, message_name, message_body):
        """ is exit """
        if message_name == 'exit' and message_body == 'exit':
            return True
        else:
            return False

    def register_message_handler(self, message_name, handler):
        """ register message handler """
        setattr(self, '%s_handler' % message_name, handler)

    def pop_message_loop(self):
        """
        pop message loop
        """
        tid = thread.get_ident()
        _logging.info('tid:%s start fast message queue consumer pop message loop',
                      tid)
        while True:
            try:
                _logging.info('tid:%s wait message', tid)
                topic, message_name, message_body = \
                       self._pub_socket.recv_multipart()
                _logging.info('tid:%s recv message', tid)
                message_body = cPickle.loads(message_body)
                _logging.info('tid:%s loads message', tid)
                if self._is_exit(message_name, message_body):
                    break
                handler = getattr(self, '%s_handler' % message_name, None)
                _logging.info('tid:%s get handler: %s', tid, handler)
                if not handler:
                    _logging.debug('topic:%s no handler message name: %s',
                                  topic, message_name)
                else:
                    _logging.debug('topic:%s process message name: %s',
                                  topic, message_name)
                    _logging.info('tid:%s start run handler', tid)
                    handler(message_body)
                    _logging.info('tid:%s end run handler', tid)
            except Exception as m:
                import traceback
                stack = [frame for frame in traceback.format_stack()]
                stack.append(str(m))
                stack = '\n'.join(stack)
                _logging.error('tid:%s message_loop exception: %s', stack)

        _logging.info('tid:%s end pop message', tid)
