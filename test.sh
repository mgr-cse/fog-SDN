#! /bin/bash
if [ -n "$2" ]; then
    ./pox.py log.level --DEBUG l2_learning_mod flow_info_extractor --filename=$1 --classifier=$2
else
    ./pox.py log.level --DEBUG l2_learning_mod flow_info_extractor --filename=$1
fi
