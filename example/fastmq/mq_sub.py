import sys
import logging
import time
from SpuFastMQ import SpuFastMQConsumer

logging.getLogger().setLevel(logging.DEBUG)

def message_handler(message):
    print message

class Consumer(SpuFastMQConsumer):
    def __init__(self, **kwargs):
        super(Consumer, self).__init__(**kwargs)

    def test_handler(self, message):
        print 'class method: %s' % message

def main(topic_key):
    conf = {
        'pub_addr' : 'tcp://*:5555',
        'topic_key' : topic_key
        }

    #fmq = SpuFastMQConsumer(**conf)
    #fmq.register_message_handler('test', message_handler)
    fmq = Consumer(**conf)
    fmq.pop_message_loop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main(None)
