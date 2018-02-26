#!/bin/bash

usage () {
    echo "$0 start|stop|list| mode"
    echo -e "\tmode: dev or pre or online"
}
case $2 in 
    dev)
        PUBLISH_PORT=9304
        DEBUG_PUBLISH_PORT=9305
        MQ_PORT=9324
        DEBUG_MQ_PORT=9325
        PUB_ADDR='tcp://10.132.62.119'
        MQ_ADDR='tcp://10.132.62.119'
        LOG_PATH='/alidata1/logs/dev/fastmq'
        IO_THREADS=1
        ;;
    pre)
        PUBLISH_PORT=9302
        DEBUG_PUBLISH_PORT=9303
        MQ_PORT=9322
        DEBUG_MQ_PORT=9323
        PUB_ADDR='tcp://10.132.62.119'
        MQ_ADDR='tcp://10.132.62.119'
        LOG_PATH='/alidata1/logs/pre/fastmq'
        IO_THREADS=1
        ;;
    online)
        PUBLISH_PORT=9300
        DEBUG_PUBLISH_PORT=9301
        MQ_PORT=9320
        DEBUG_MQ_PORT=9321
        PUB_ADDR='tcp://10.132.62.119'
        MQ_ADDR='tcp://10.132.62.119'
        LOG_PATH='/alidata1/logs/online/fastmq'
        IO_THREADS=1
        ;;
    *)
        usage
        ;;
esac

TIME=$(date +%Y-%m-%d:%H:%M:%S)

command_start () {
    nohup python fastmq_server --pub_addr=$PUB_ADDR:$PUBLISH_PORT --mq_addr=$MQ_ADDR:$MQ_PORT --io_threads=$IO_THREADS $1 > $LOG_PATH/fastmq.$1.$TIME.log  2>&1 &
    # debug
    #nohup python fastmq_server $1 --debug=True --pub_addr=$PUB_ADDR:$DEBUG_PUBLISH_PORT --mq_addr=$MQ_ADDR:$DEBUG_MQ_PORT > $LOG_PATH/fastmq.debug.$1.$TIME.log &
    ps -ef | grep fastmq_server | grep $1 |grep -v 'grep'
    exit 0
}
command_stop () {
    if ps -ef | grep fastmq_server | grep $1 | grep -v 'grep' | awk '{print $2}' | xargs kill -9; then
        echo 'stop success'
    fi
    exit 0
}
command_list () {
    ps -ef | grep fastmq_server | grep $1 |grep -v 'grep'
    exit 0
}

command_$1 $2
