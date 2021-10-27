#!/bin/bash

echo trbcmd reset
trbcmd reset

#sleep 3
echo addresses.sh
./addresses.sh

# set correct timeout: off for channel 0, 1, 2sec for 2
trbcmd w 0xfffe 0xc5 0x50ff
trbcmd loadbit 0xfe91 0xc5 0xffff0000 0x00080000
trbcmd loadbit 0xfe90 0xc5 0xffff0000 0x00060000
trbcmd loadbit 0xfe45 0xc5 0xffff0000 0x00040000


#cd /daqtools/xml-db
#trbcmd w 0x 0x7111 0x00720072
##./put.pl Readout 0xfe51 SetMaxEventSize 500
#cd -


echo loadregisterdb.pl register_configgbe.db
echo loadregisterdb.pl register_configgbe_ip.db

#~/trbsoft/daqtools/tools/loadregisterdb.pl register_configgbe.db
#~/trbsoft/daqtools/tools/loadregisterdb.pl register_configgbe_ip.db
/daqtools/tools/loadregisterdb.pl register_configgbe.db
/daqtools/tools/loadregisterdb.pl register_configgbe_ip.db
#sleep 1

echo ./conf_tdcs.sh
./conf_tdcs.sh
# setting the VOVA tdc to  default settings and max thresholds
trbcmd w 0x1801 0xA002 0x00000000
trbcmd w 0x1801 0xA003 0x00000000
trbcmd w 0x1801 0xAA00 0x00000000
trbcmd w 0x1801 0xA203 0xffffffff
trbcmd w 0x1801 0xA213 0xffffffff
trbcmd w 0x1801 0xA223 0xffffffff
trbcmd w 0x1801 0xA233 0xffffffff



echo ./conf_cts.sh
./conf_cts.sh
