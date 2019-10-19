#!/bin/bash

#name=$(basename $(pwd))
name=go4

docker build -t $name . || exit

docker run --net host -v $(pwd)/conf:/conf -v $(pwd)/workdir:/workdir \
--name $name \
--rm -it --user $(id -u) $name \
 /workdir/start.sh
