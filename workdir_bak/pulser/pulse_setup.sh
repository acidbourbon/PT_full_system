
# set up bith channels of frequency generator

vxi11_cmd tekafg "SOUR1:FREQ 1000"   
vxi11_cmd tekafg "SOUR1:VOLT:LEV:HIGH 350mV"
vxi11_cmd tekafg "SOUR1:VOLT:LEV:LOW 0mV"
vxi11_cmd tekafg "SOUR1:VOLT:LEV:OFFS 0mV"
vxi11_cmd tekafg "SOUR1:PULS:WIDT 200n"
vxi11_cmd tekafg "SOUR1:PULS:DEL 0"
vxi11_cmd tekafg "SOUR1:PULS:TRAN:LEAD 3ns"
vxi11_cmd tekafg "SOUR1:PULS:TRAN:TRA 3ns"
vxi11_cmd tekafg "OUTP1:POL INV"

vxi11_cmd tekafg "SOUR2:FREQ 1000"
vxi11_cmd tekafg "SOUR2:VOLT:LOW 0mV"
vxi11_cmd tekafg "SOUR2:VOLT:LEV:HIGH 2500mV"
vxi11_cmd tekafg "SOUR2:VOLT:OFFS 0mV"
vxi11_cmd tekafg "SOUR2:PULS:WIDT 300n"
vxi11_cmd tekafg "SOUR2:PULS:DEL 0"
vxi11_cmd tekafg "SOUR2:PULS:TRAN:LEAD 25ns"
vxi11_cmd tekafg "SOUR2:PULS:TRAN:TRA 50ns"
vxi11_cmd tekafg "OUTP2:POL NORM"

vxi11_cmd tekafg "OUTP1:STAT ON"

  

