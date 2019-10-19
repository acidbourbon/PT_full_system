docker build -t go4 . || exit
#xhost +si:localuser:root
docker run --net host -v $(pwd)/conf:/conf -v $(pwd)/workdir:/workdir --rm -it \
--name go4 \
go4 /workdir/start.sh

#-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY \

