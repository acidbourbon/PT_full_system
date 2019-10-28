docker build -t go4 . || exit
#xhost +si:localuser:root
docker run --net host -v $(pwd)/conf:/conf -v $(pwd)/workdir:/workdir --rm -it \
--device /dev/ttyUSB2:/dev/ttyUSB_micos_eco \
--device /dev/ttyUSB1:/dev/ttyUSB_HAMEG_TRB \
--device /dev/ttyUSB3:/dev/ttyUSB_phidrive \
--device /dev/ttyACM0:/dev/ttyUSB_wallplugs \
--name go4 \
go4 /workdir/start.sh

#-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY \

