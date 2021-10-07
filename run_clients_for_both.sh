#!/usr/bin/env bash

source ~/python_environment/pero_ocr_web_clients/bin/activate
export PYTHONPATH=/home/pero/pero/pero-ocr:/home/pero/pero/pero_ocr_web
export TF_CUDNN_USE_AUTOTUNE=0

LOG_DATE=$(date '+%Y%m%d%H%M%S')
while true
do
    python3 -u /home/pero/pero/pero-ocr-api/processing_client/run_client.py -c /home/pero/pero/pero-ocr-api/processing_client/config-example.ini --time-limit 0.3 --exit-on-done 2>&1 | tee -a api.$LOG_DATE.txt
    sleep 2
    python -u run_clients.py --time-limit 0.02 2>&1 | tee -a log.$LOG_DATE.txt
    sleep 2
done

