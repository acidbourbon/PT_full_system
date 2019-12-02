docker kill fst
docker build -t fst . || exit
#xhost +si:localuser:root
docker run --net host -v $(pwd)/conf:/conf -v $(pwd)/workdir:/workdir --rm -it \
--name fst \
fst /workdir/start.sh

#-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY \
#--device /dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo_phidrive-if00:/dev/ttyUSB_phidrive \
#--device /dev/serial/by-id/usb-Arduino_LLC_Arduino_Leonardo-if00:/dev/ttyUSB_wallplugs \
#--device /dev/serial/by-id/usb-FTDI_USB__-__Serial-if00-port0:/dev/ttyUSB_micos_eco \
#--device /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_023192710-if00-port0:/dev/ttyUSB_HAMEG_TRB \
#--device /dev/serial/by-id/usb-HAMEG_HAMEG_HO720_020546035-if00-port0:/dev/ttyUSB_HAMEG_LV \

