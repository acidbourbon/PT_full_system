docker build -t go4_mdc . || exit
#xhost +si:localuser:root
docker run --net host -v  $(pwd)/../workdir:/old -v $(pwd)/conf:/conf -v $(pwd)/workdir:/workdir --rm -it \
--name go4_mdc \
go4_mdc /workdir/start.sh

#-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY \

