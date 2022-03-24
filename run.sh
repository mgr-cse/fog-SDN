#!/bin/bash

# tunable parameters
hosts="$1"
maxRuns="10"

# dump host number
echo $hosts > tempFiles/numHost.txt

# generate sample ips
./generateIPs.py $hosts

# run for max runs
for i in $(seq 1 1 "$maxRuns"); do
    # dump runId
    echo $i > tempFiles/runId.txt

    # start pox
    ./test.sh test$i.txt &
    POXPID=$!
    sleep 5

    # start mininet
    ./single_sw_N_host_up.sh

    # kill pox
    kill $POXPID
    killall python3

    echo run $i complete!
done

rm -r pox-data/$hosts
mkdir -p pox-data/$hosts/{pcaps,poxLogs}
mv pcaps/* pox-data/$hosts/pcaps/
mv poxLogs/* pox-data/$hosts/poxLogs/
