#!/bin/bash

# tunable parameters
hosts="$1"
classifier="$2"

# select last 4 runs
selectRuns=`seq 7 1 10`


# dump host number
echo $hosts > tempFiles/numHost.txt

# run for max runs
for i in $selectRuns; do
    # dump runId
    echo $i > tempFiles/runId.txt

    # start pox
    ./test.sh test$i.txt $hosts/$2 &
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
mkdir -p ./test-data/$classifier/$hosts/
cp ./poxLogs/* ./test-data/$classifier/$hosts/
mv ./poxLogs/* ./replay-data/$hosts/
