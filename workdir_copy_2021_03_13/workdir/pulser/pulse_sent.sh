# sent out pulses for 1 second  = 10000 pulses

echo " Pulser ON for 1 second = 10000 pules "
# vxi11_cmd tekafg "OUTP1:STAT ON"
 vxi11_cmd tekafg "OUTP2:STAT ON"  

 sleep 1

 #vxi11_cmd tekafg "OUTP1:STAT OFF"
 vxi11_cmd tekafg "OUTP2:STAT OFF"  
echo " Pulser off, finished. "

  

