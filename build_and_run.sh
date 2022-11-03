docker build -t go4_mdc . || exit
#xhost +si:localuser:root
docker run --net host -v  $(pwd)/../workdir:/old -v $(pwd)/conf:/conf -v $(pwd)/workdir:/workdir  -v /local/mdc:/local --rm -it \
--name go4_mdc \
--device /dev/serial/by-id/usb-Silicon_Labs_Seeeduino_Nano_0001-if00-port0:/dev/ttyPANDAmux \
go4_mdc /workdir/start.sh

#-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY \

