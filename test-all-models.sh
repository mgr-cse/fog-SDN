#!/bin/bash

hosts="10 20 40 80"
models="dtree_depth5 dtree_depth10 random_forest50_depth10 lin_logloss_sgd_stop10 lin_logloss_sgd_stop15 lin_logloss_sgd_nostop"

for host in $hosts; do
    for m in $models; do
        echo $host $m
        ./run-replay.sh $host $m
        ./test-ml-models.py $host
    done
done