
for TDC in 0x0351; do



	# set trigger on the horizontal scintillator
	trbcmd w $TDC 0xdf00 $(perl -e "printf(\"0x%X\", 0b01000000000000000000000000000000 )")
	trbcmd w $TDC 0xdf01 $(perl -e "printf(\"0x%X\", 0b00000000000000000000000000000000 )")

	# trigger stretch
	trbcmd w $TDC 0xdf20 $(perl -e "printf(\"0x%X\", 0b00000000000000000000000000000100 )")
	# trigger invert
	trbcmd w $TDC 0xdf24 $(perl -e "printf(\"0x%X\", 0b00000000000000000000000000000100 )")

done

cd /workdir
./set_ref_chan_scinti.py
