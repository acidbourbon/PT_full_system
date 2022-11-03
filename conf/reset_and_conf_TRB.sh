#!/bin/bash

echo trbcmd reset
trbcmd reset

#sleep 3
echo addresses.sh
./addresses.sh

# set correct timeout: off for channel 0, 1, 2sec for 2
trbcmd w 0xfffe 0xc5 0x50ff

#cd /daqtools/xml-db
#trbcmd w 0x 0x7111 0x00720072
##./put.pl Readout 0xfe51 SetMaxEventSize 500
#cd -


echo /daqtools/tools/loadregisterdb.pl register_configgbe.db
echo /daqtools/tools/loadregisterdb.pl register_configgbe_ip.db

/daqtools/tools/loadregisterdb.pl register_configgbe.db
/daqtools/tools/loadregisterdb.pl register_configgbe_ip.db
#sleep 1

echo ./conf_tdcs.sh
./conf_tdcs.sh

echo ./conf_cts.sh
./conf_cts.sh
