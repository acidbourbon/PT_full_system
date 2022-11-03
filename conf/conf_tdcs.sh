#!/bin/bash
# ** eanble  scaler monitor  tor TDCs: 
trbcmd w 0x1000 0xdf80  0xffffffff

trbcmd w 0x1000 0xc801  0  #no trigger windows
trbcmd w 0x1000 0xc802  0x00ff  #enable 8 channels
trbcmd w 0x1000 0xc804  10  #max 10 words per channel
trbcmd w 0x1000 0xc805 0xFFFF # invert channels for correct signal readout

for TDC in 0x0350 0x0351 0x0352 0x0353 0x1500 0x1501 0x1502 0x1503; do

	# invert the first 32 channels
	#trbcmd w $TDC 0xc805 0xFFFFFFFF


	# enable trigger windows +-1000 ns
# 	trbcmd w $TDC 0xc801 0x814000c8

	# set channel ringbuffer size
# 	trbcmd w $TDC 0xc804 10

done


### tdcs with pasttrec attached ###

for TDC in 0x0350 0x0351 0x0352 0x0353 0x1500 0x1501 0x1502 0x1503; do

	# invert the first 48 channels 
# 	trbcmd w $TDC 0xc805 0xFFFFFFFF
# 	trbcmd w $TDC 0xc806 0xFFFF

done


# PASTTREC TDC #

for TDC in 0x0350; do
	# invert the first 48 channels 
# 	trbcmd w $TDC 0xc805 0xFFFFFFFF
# 	trbcmd w $TDC 0xc806 0xFFFF

	# non- invert the first channel 
	#trbcmd clearbit $TDC 0xc805 0x1
	
	# enable the first channel
	#trbcmd setbit $TDC 0xc802 0x1

	# enable the first two PASTTRECS
	#trbcmd setbit $TDC 0xc802 0xFFFFFFFF

	# enable the 49th channel
# 	trbcmd setbit $TDC 0xc803 0x10000

	# enable trigger for 49th channel
#         trbcmd setbit $TDC 0xdf01 0x10000

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

#for TDC in 0x0351; do
#
#
#	# enable the first two CONNS for PADIWA and Scintis
#	#trbcmd setbit $TDC 0xc802 0xFFFFFFFF
#
#	# enable the PADIWA chans and the scintillators
#	trbcmd w $TDC 0xc802 $(perl -e "printf(\"0x%X\", 0b01010000000010010000000000001100 )")
#	#trbcmd w $TDC 0xc802 0x5009000C
#
#	# invert the si_strip
#	trbcmd w $TDC 0xc805 $(perl -e "printf(\"0x%X\", 0b00000000000000000000000000000100 )")
#
#	# set trigger on the horizontal scintillator
#	trbcmd w $TDC 0xdf00 $(perl -e "printf(\"0x%X\", 0b01000000000000000000000000000000 )")
#	trbcmd w $TDC 0xdf01 $(perl -e "printf(\"0x%X\", 0b00000000000000000000000000000000 )")
#
#	# trigger stretch
#	trbcmd w $TDC 0xdf20 $(perl -e "printf(\"0x%X\", 0b00000000000000000000000000000100 )")
#	# trigger invert
#	trbcmd w $TDC 0xdf24 $(perl -e "printf(\"0x%X\", 0b00000000000000000000000000000100 )")
#
#done
