#!/bin/bash
for TDC in 0x0350 0x0351 0x0352 0x0353 0x1500 0x1501 0x1502 0x1503; do

	# invert the first 32 channels
	#trbcmd w $TDC 0xc805 0xFFFFFFFF

	# invert the first 48 channels 
	trbcmd w $TDC 0xc805 0x0
	trbcmd w $TDC 0xc806 0x0

	# enable trigger windows +-1000 ns
	trbcmd w $TDC 0xc801 0x814000c8

	# set channel ringbuffer size
	trbcmd w $TDC 0xc804 10

done

