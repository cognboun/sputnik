#!/bin/bash

usage () {
    echo "$0 start|stop|list| mode"
    echo -e "\tmode: dev or pre or online"
}
case $2 in 
    dev)
        PORT=9284
        DEBUG_PORT=9385
        LOG_PATH='/alidata1/logs/dev/spumaster'
        ;;
    pre)
        PORT=9282
        DEBUG=9283
        LOG_PATH='/alidata1/logs/pre/spumaster'
        ;;
    online)
        PORT=9280
        DEBUG_PORT=9281
        LOG_PATH='/alidata1/logs/online/spumaster'
        ;;
    *)
        usage
        ;;
esac

TIME=$(date +%Y-%m-%d:%H:%M:%S)

command_start () {
    nohup python spumaster_server --port=$PORT $1> $LOG_PATH/spumaster.$1.$TIME.log 2>&1 &
    # debug
    #nohup python spumaster_server $1 --app_port=$DEBUG_PORT --debug=True > $LOG_PATH/spumaster.debug.$1.$TIME.log &
    ps -ef | grep spumaster_server | grep $1 | grep -v 'grep'
    exit 0
}
command_stop () {
    if ps -ef | grep spumaster_server | grep $1 | grep -v 'grep' | awk '{print $2}' | xargs kill -9; then
        echo 'stop success'
    fi
    exit 0
}
command_list () {
    ps -ef | grep spumaster_server | grep $1 | grep -v 'grep'
    exit 0
}

command_$1 $2
