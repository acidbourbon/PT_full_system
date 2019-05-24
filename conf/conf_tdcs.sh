#!/bin/bash
for TDC in 0x0350 0x0351 0x0352 0x0353 0x1500 0x1501 0x1502 0x1503; do

	# invert the first 32 channels
	#trbcmd w $TDC 0xc805 0xFFFFFFFF

	# invert the first 48 channels 
	trbcmd w $TDC 0xc805 0xFFFFFFFF
	trbcmd w $TDC 0xc806 0xFFFF

	# enable trigger windows +-1000 ns
	trbcmd w $TDC 0xc801 0x814000c8

	# set channel ringbuffer size
	trbcmd w $TDC 0xc804 10

done


### tdcs with pasttrec attached ###

for TDC in 0x0350 0x0351; do

	# enable the first 16 channels (CONN1)
	 #trbcmd setbit $TDC 0xc802 0x0000FFFF

	# enable the second 16 channels (CONN2)
	#trbcmd setbit $TDC 0xc802 0xFFFF0000
       echo "do nothing here"

done


### reference time TDC ###

for TDC in 0x0350; do

	# non- invert the first channel 
	#trbcmd clearbit $TDC 0xc805 0x1
	
	# enable the first channel
	#trbcmd setbit $TDC 0xc802 0x1

	# enable the 49th channel
	trbcmd setbit $TDC 0xc803 0x10000

	# enable trigger for 49th channel
        trbcmd setbit $TDC 0xdf01 0x10000

	# enable Florian's trigger Logic
	#trbcmd setbit $TDC 0xe000 0x1
	# enable edge detect
	#trbcmd setbit $TDC 0xe008 0x1
	# merge outputs
	#trbcmd setbit $TDC 0xe018 0x1
	# delay 0 cycles
	#trbcmd setbit $TDC 0xe100 0x0
	# stretcher on, five cycles
	#trbcmd setbit $TDC 0xe200 0x10005
        echo " --- "

done
