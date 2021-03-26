#!/bin/bash

for i in $@; do
  echo "reloading fpga $i"
  echo "trbcmd reload $i"
  trbcmd reload $i
done

sleep 4

echo "re-addressing"
echo "../conf/addresses.sh"
../conf/addresses.sh

echo "reconfiguring"
echo "../conf/conf_tdcs.sh"
../conf/conf_tdcs.sh

echo "enable/disable active channels of active boards"
./enable_active_channels.py
