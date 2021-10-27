
#!/bin/bash
alias i='trbcmd i 0xffff'

#  new MDC MBO for mbo_check.py 
#trbcmd s 0x00009b7400202941  0x01 0x1898
#trbcmd s 0x0000f5a1001f2941  0x01 0x1899
#trbcmd s 0x0000fe5c001f2941  0x01 0x8099


# set address for second TDC on short MBO:
#board no. 001  - Lena right board
trbcmd s 0x0000f34c001f2941 0x01 0x1800
trbcmd s 0x00009c7d00202941 0x01 0x1801

#board no. 002
trbcmd s 0x0000f069001f2941 0x01 0x1802 #quite weak readout from channel 12 (norm 0, but when you touch flex - increases) - same board on different MBO are okay
trbcmd s 0x0000fdd3001f2941 0x01 0x1803 # OK

#board no. 004    ----   missing second MDC TDC flashing goes ok, but after short PC second FPGA doesn't work (I think that there is something wrong with default image memory)
#trbcmd s 0x0000618f00752941 0x01 0x1804  
#trbcmd s 0x0000770800752941 0x01 0x1805
#
#echo "4 done"
#board no. 005
trbcmd s 0x0000243900752941 0x01 0x1806  # OK
trbcmd s 0x0000606100752941 0x01 0x1807  # OK


echo "5 done"
#board no. 006
trbcmd s 0x0000238000752941 0x01 0x1808 # weak readout from channel 12(20kHz) and 27 (0) (but when you touch flex - increases/swapping the DBO solved the problem)
trbcmd s 0x00001dcd00752941 0x01 0x1809 # OK

#board no. 007
trbcmd s 0x0000905200752941 0x01 0x1810 # weak readout from channel 3/12/26/32 (but when you touch flex - increases)
trbcmd s 0x00008fe100752941 0x01 0x1811 # OK

#board no. 008
trbcmd s 0x000090d700752941 0x01 0x1812 # weak readout from channel 3/27/23 (but when you touch flex - increases)
trbcmd s 0x0000766e00752941 0x01 0x1813 # OK

#board no. 009
trbcmd s 0x00001e4a00752941 0x01 0x1814 # weak readout from channel 27  (10kHz) (but when you touch flex - increases)
trbcmd s 0x0000064e00752941 0x01 0x1815 # OK
#
#board no. 010
trbcmd s 0x0000432d00752941 0x01 0x1816 # weak readout from channel 26/27  (70/20kHz) (but when you touch flex - increases)
trbcmd s 0x000090d200752941 0x01 0x1817 # OK
#
#echo "10 done"
#board no. 011
trbcmd s 0x000024b200752941 0x01 0x1818 # weak readout from channel 3/19/27 (1/10/20 kHz) (but when you touch flex - increases)
trbcmd s 0x00003be300752941 0x01 0x1819 # weak readout from channel 6 (0) (but when you touch flex - increases)

#board no. 012
trbcmd s 0x0000028200752941 0x01 0x1820 # weak readout from channel 3/26 (40/0 kHz) (but when you touch flex - increases)
trbcmd s 0x0000ede000742941 0x01 0x1821 # weak readout from channel 4/6 (0/0 kHz) (but when you touch flex - increases)

#board no. 013		----	after programming FPGA it doesn't show up in network map probably faulty oscilator in one of the FPGAs 
#board no. 014		----	missing one PASTREC

#board no. 015  -- Lena left board
trbcmd s 0x00009b7400202941 0x01 0x1822
trbcmd s 0x0000f5a1001f2941 0x01 0x1823

  #hub
trbcmd s 0x0000e4b3001f2941 0x01 0x8001

trbcmd s 0x0000e6cf001f2941 0x01 0x8002

#trbcmd s 0x000006de00752941 0x01 0x8004
#
trbcmd s 0x00001eaa00752941 0x01 0x8005

trbcmd s 0x0000039800752941 0x01 0x8006

trbcmd s 0x000090a000752941 0x01 0x8007
#
trbcmd s 0x000009d700762941 0x01 0x8008
trbcmd s 0x0000023000752941 0x01 0x8009
trbcmd s 0x000060a900752941 0x01 0x8010
trbcmd s 0x0000904400752941 0x01 0x8011
trbcmd s 0x00001ea600752941 0x01 0x8012
trbcmd s 0x0000fe5c001f2941 0x01 0x8015
# enable scalers
trbcmd w 0xfe91 0xdf80  0xffffffff
trbcmd w 0xfe91 0xdf85  0xffffffff
trbcmd w 0xfe91 0xdf87  0xffffffff
#switch 10 TDC channels to wires  in beam focus @COSY May 2021
#trbcmd loadbit 0x1801 0xd580 0x300 0x000
#trbcmd loadbit 0x1802 0xd580 0x300 0x200
#trbcmd loadbit 0x1803 0xd580 0x300 0x000
#trbcmd loadbit 0x1800 0xd580 0x300 0x200


for TDC in 0x0350 0x0351 0x0352 0x0353 0x1500 0x1501 0x1502 0x1503 0x1800 0x1801 0x1802 0x1803 0xfe91 ; do

	# invert the first 32 channels
	#trbcmd w $TDC 0xc805 0xFFFFFFFF


	# enable trigger windows +-1000 ns
	trbcmd w $TDC 0xc801 0x814000c8

	# set channel ringbuffer size
	trbcmd w $TDC 0xc804 10

        # enable the 49th channel
        trbcmd setbit $TDC 0xc803 0x10000

        # enable trigger for 49th channel
        trbcmd setbit $TDC 0xdf01 0x10000


done


### tdcs with pasttrec attached ###

for TDC in 0x0350 0x0351 0x0352 0x0353 0x1500 0x1501 0x1502 0x1503; do

	# invert the first 48 channels  for TDC with PANDA boards input
	# do not invert channels for newMBO TDC with 10 channels
	trbcmd w $TDC 0xc805 0xFFFFFFFF
	trbcmd w $TDC 0xc806 0xFFFF

done


# PASTTREC TDC #

#for TDC in 0x0350 0x0351 0x0352 0x0353 0x1500 0x1501 0x1502 0x1503  0x1800 0x1801; do

	# non- invert the first channel 
	#trbcmd clearbit $TDC 0xc805 0x1
	
	# enable the first channel
	#trbcmd setbit $TDC 0xc802 0x1

	# enable the first two PASTTRECS
	#trbcmd setbit $TDC 0xc802 0xFFFFFFFF

	# enable the 49th channel
#	trbcmd setbit $TDC 0xc803 0x10000

	# enable trigger for 49th channel
#       trbcmd setbit $TDC 0xdf01 0x10000

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
#       echo " --- "

#done

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
#### 

