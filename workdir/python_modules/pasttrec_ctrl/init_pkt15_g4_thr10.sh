#!/bin/bash

for CONN in 1 2; do
	for CHIP in 0 1; do

		./spi black_settings_pt15_g1_thr127
		pktime=15 gain=4 ./set_gain_pktime
		./threshold 10

	done
done
