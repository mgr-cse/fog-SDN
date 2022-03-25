#!/bin/bash

# tunable parameters
hosts="$1"

# select last 4 runs
selectRuns=`seq 6 1 10`


# dump host number
echo $hosts > tempFiles/numHost.txt

# run for max runs
for i in $selectRuns; do
    # dump runId
    echo $i > tempFiles/runId.txt

    # start pox
    ./test.sh test$i.txt &
    POXPID=$!
    sleep 5

    # start mininet
    ./replay.sh

    # kill pox
    kill $POXPID
    killall python3

    echo run $i complete!
done

mkdir -p ./replay-data/$hosts
mv ./poxLogs/* ./replay-data/$hosts/
