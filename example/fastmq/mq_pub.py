import logging
import time
from SpuFastMQ import SpuFastMQProducer

logging.getLogger().setLevel(logging.DEBUG)

def main():
    conf = {
        'mq_addr' : 'tcp://*:2222',
        'topic_key' : 'test_topic1'
        }

    fmq = SpuFastMQProducer(**conf)
    print fmq.push_message('test', ['asdf', {'a':13, 'b':'asdf'}])
    time.sleep(2)
    conf = {
        'mq_addr' : 'tcp://*:2222',
        'topic_key' : 'test_topic2'
        }

    fmq = SpuFastMQProducer(**conf)
    print fmq.push_message('test', ['asdf', {'a':13, 'b':'asdf'}])
    time.sleep(2)
    fmq.stop_message_queue_server()

if __name__ == "__main__":
    main()
