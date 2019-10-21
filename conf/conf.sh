#!/bin/bash

cd /conf



echo "configure container"

export TRB3_PORT=35
export DAQOPSERVER=localhost:$TRB3_PORT
export TRB3_SERVER=192.168.4.240
export CTS_GUI_PORT=1148
export CTS_ENDPOINT=0xc035
export DISPLAY=:2 # go4 window will be sent to $DISPLAY, if provide_vnc == yes , then it will be this x11 display

export PULSER=192.168.103.74

> conf_log.txt

provide_dhcp=yes
#edit conf/dhcpd.conf, enter your trb3 MAC address ###
provide_trbnetd=yes

provide_cts_gui=yes

provide_vnc=yes
vnc_password=1234
vnc_port=5902
vnc_geometry=1500x1024


#   tmux new-session -d -s x11vnc -n x11vnc "x11vnc -forever -create -rfbport 5902 #(nopasswd)"

# set paths for go4/dabc/stream
. /trb3/trb3login



### no need to touch the rest of the file ###

  echo ... >> conf_log.txt
  echo DAQOPSERVER=$DAQOPSERVER >> conf_log.txt
  echo >> conf_log.txt

if [ $provide_dhcp == "yes" ]; then
  echo starting dhcp server
  # for opensuse
  #cp dhcpd.conf /etc/dhcpd.conf
  # for ubuntu
  cp dhcpd.conf /etc/dhcp/dhcpd.conf

  > /tmp/dhcp_leasefile
  dhcpd -lf /tmp/dhcp_leasefile >> conf_log.txt 2>&1
  echo ... >> conf_log.txt
  echo dhcp server started >> conf_log.txt
  echo using config file /conf/dhcpd.conf >> conf_log.txt
  echo >> conf_log.txt
fi

if [ $provide_trbnetd == "yes" ]; then
  trbnetd -i $TRB3_PORT
  echo ... >> conf_log.txt
  echo started trbnetd >> conf_log.txt
  echo TRB3_SERVER=$TRB3_SERVER >> conf_log.txt
  echo port $TRB3_PORT >> conf_log.txt
  echo >> conf_log.txt
fi

if [ $provide_cts_gui == "yes" ]; then
#   screen -S cts_gui -d -m ./start_cts_gui.sh
  tmux new-session -d -s cts_gui -n cts_gui "cd /daqtools/web; perl ./cts_gui --endpoint $CTS_ENDPOINT --quiet --noopenxterm --port $CTS_GUI_PORT"
#   tmux new-window -t main:1 -n "cts_gui" "cd /daqtools/web; perl ./cts_gui --endpoint $CTS_ENDPOINT --quiet --noopenxterm --port $CTS_GUI_PORT"
  echo ... >> conf_log.txt
  echo started cts_gui with following parameters:>> conf_log.txt
  echo --endpoint $CTS_ENDPOINT >> conf_log.txt
  echo --port $CTS_GUI_PORT >> conf_log.txt
  echo >> conf_log.txt
fi

if [ $provide_vnc == "yes" ]; then
  mkdir -p $HOME/.vnc/
  cp /conf/xstartup $HOME/.vnc/xstartup
  chmod +x $HOME/.vnc/xstartup
  echo $vnc_password | vncpasswd -f > $HOME/.vnc/passwd
  tmux new-session -d -s vnc -n vnc "echo starting vnc server on port $vnc_port for display $DISPLAY; vncserver $DISPLAY -rfbauth $HOME/.vnc/passwd -rfbport $vnc_port -geometry $vnc_geometry ;/bin/bash"
  
  echo ... >> conf_log.txt
  echo "started vnc server (e.g. for Go4 window)" >> conf_log.txt
  echo port=$vnc_port >> conf_log.txt
  echo DISPLAY=$DISPLAY >> conf_log.txt
  echo password=$vnc_password >> conf_log.txt
  echo >> conf_log.txt
  echo connect with:   vncviewer localhost:$vnc_port >> conf_log.txt
  echo >> conf_log.txt
fi


./reset_and_conf_TRB.sh


echo "done"
