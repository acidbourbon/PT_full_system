#!/bin/bash

sec=$1 
label=$2

rm /workdir/data/*.hld
killall dabc_exe
dabc_exe TdcEventBuilder.xml &
dabcpid=$!
sleep $sec # wait $sec seconds
kill -s SIGINT $dabcpid # send termination signal to go4analysis
wait # wait for go4analysis to finish

timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
target_dir=/workdir/data/${timestamp}_${label}

mkdir -p $target_dir
mv /workdir/data/*.hld $target_dir/

echo acquisition complete


