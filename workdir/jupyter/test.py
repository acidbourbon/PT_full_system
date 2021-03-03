#!/usr/bin/env python
# coding: utf-8

# In[33]:


#pulse generator
#import rigol as pulsgenerator 
#pulsgenerator.output_on('2')
#pulsgenerator.output_off('2')

import os
import time
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3AOUTPUT2%20ON'")
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3AFREQ%201000'")
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3AVOLT%3ALEV%3AHIGH%202500mV'")
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3AVOLT%3ALEV%3ALOW%200mV'")
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3AVOLT%3ALEV%3AOFFS%200mV'")
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3APULS%3ADEL%200'")
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3APULS%3AWIDT%20300n'")
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3APULS%3ATRAN%3ALEAD%2025ns'")
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3APULS%3ATRAN%3ATRA%2050ns'")
#os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42'")
#os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42'")
#os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42'")
#os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42'")

#os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3AOUTPUT2%20OFF'")



#vxi11_cmd tekafg "SOUR1:FREQ 1000"   
#vxi11_cmd tekafg "SOUR1:VOLT:LEV:HIGH 350mV"
#vxi11_cmd tekafg "SOUR1:VOLT:LEV:LOW 0mV"
#vxi11_cmd tekafg "SOUR1:VOLT:LEV:OFFS 0mV"
#vxi11_cmd tekafg "SOUR1:PULS:WIDT 200n"
#vxi11_cmd tekafg "SOUR1:PULS:DEL 0"
#vxi11_cmd tekafg "SOUR1:PULS:TRAN:LEAD 3ns"
#vxi11_cmd tekafg "SOUR1:PULS:TRAN:TRA 3ns"
#vxi11_cmd tekafg "OUTP1:POL INV"

#vxi11_cmd tekafg "SOUR2:FREQ 1000"
#vxi11_cmd tekafg "SOUR2:VOLT:LOW 0mV"
#vxi11_cmd tekafg "SOUR2:VOLT:LEV:HIGH 2500mV"
#vxi11_cmd tekafg "SOUR2:VOLT:OFFS 0mV"
#vxi11_cmd tekafg "SOUR2:PULS:WIDT 300n"
#vxi11_cmd tekafg "SOUR2:PULS:DEL 0"
#vxi11_cmd tekafg "SOUR2:PULS:TRAN:LEAD 25ns"
#vxi11_cmd tekafg "SOUR2:PULS:TRAN:TRA 50ns"
#vxi11_cmd tekafg "OUTP2:POL NORM"

#vxi11_cmd tekafg "OUTP1:STAT ON"
for freq in [10,100,1000,10000,1000000]:
    #os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3AFREQ%20{:d}'".format(freq))
    time.sleep(4)
    print(freq)
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&OUTPUT2%20OFF'")


# In[20]:


os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&OUTPUT2%20ON'")


# In[39]:


##s-curve (threshold) scan
import os
from matplotlib import pyplot as plt
import numpy as np
import pasttrec_ctrl as ptc
import tdc_daq as td
import baseline_calib
import db
from cw_pasttrec_functions import *
name="4000"
#pulse generator, switch channel 2 on
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3AOUTPUT2%20ON'")
for freq in [50000,100000,200000,500000]:
#if True:
    os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3AFREQ%20{:d}'".format(freq))

    ptc.init_active_boards()  
    print("threshold scan, at baseline from config")
    baseline_calib.char_noise_by_thresh_scan(name,dummy_calib=True)    
    #read threshold_scan from database:
    dummy_calib = db.get_calib_json_by_name(name,dummy_calib=True)
    tsbl_scan_raw = dummy_calib["tsbl_scan_raw"]
    tsbl_range    = dummy_calib["tsbl_range"]

     #plot current scan results for all channels:

    # threshold scan
    plt.rcParams["figure.figsize"] = (8,6)
    del tsbl_range[:1] 
    for i in range(3,4):
      del tsbl_scan_raw[i][:1] 
      plt.scatter(tsbl_range,tsbl_scan_raw[i],alpha=0.2,label = "{:d}".format(i))

      plt.legend()
      plt.xlabel(" threshold LSB ( 2mV / LSB ) ")
      plt.ylabel("mean pulse rate (Hz)")
      #plt.yscale('log') 
      plt.show()
#pulse generator, switch channel 2 off   
os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3AOUTPUT2%20OFF'")


