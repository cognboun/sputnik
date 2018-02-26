#!/bin/bash

python ../service/webservice.py --server_port=8888 --app_port=8890 --debug=True ../conf/webservice_config
#nohup python ../service/webservice.py --server_port=8888 --app_port=8889 --log_file_prefix=./webservice.log ../conf/webservice_config &
