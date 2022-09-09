#!/usr/bin/env python3

# ------ standart Python classes ---------

import os
import time
import sys, tty, termios
import threading
#import json
from numpy import *
#from glob import glob

# ------ PANDa specified classes ---------
sys.path.append(os.path.split(os.path.realpath(__file__))[0]+"/Devices")

from config import *

# -- laboratory equipment --
from signal_generator import signal_generator


# ---- initializing laboratory equipment ----

gen = signal_generator("ip:192.168.0.197:5025")
gen.initialize((1,2))
print("signal generator ON !")
gen.set_output_state((1,2),1 )

# --- Charge Injectors configuration ----------
from PANDAmux import PANDAinjectors
Injectors = PANDAinjectors()

#print("signal generator 10kHz !")

#for freq in [1.,2.,3.,4.,5.]:

gen.set_amplitude((1,2), 3.0 )
	#time.sleep(1)
	#for freq in [10,100,1000,10000]:
	
		#gen.set_frequency((1,2), freq )
		#print(freq)
		#time.sleep(1)
	
	
	
#print("signal generator off !")
#gen.set_output_state((1,2),0 )
Injectors.setActiveChannel(4)


import pasttrec_ctrl as pasttrec_ctrl
#Thresholds = [5, 10, 13,15,18,20,22,25]
Thresholds = [ 10]
#pasttrec_ctrl.init_board_by_name("4000", 15 ,4, 5)

for chan in range(0,8):

	#Injectors.setActiveChannel(chan)
	#print (chan, " active channel = ", Injectors.getActiveChannels())

	for th in Thresholds:
		pasttrec_ctrl.set_threshold_for_board_by_name("4000",th)
		print(th)
		time.sleep(1)
		
