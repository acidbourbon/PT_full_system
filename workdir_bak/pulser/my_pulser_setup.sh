#!/bin/bash

## set burst trigger to 500 Hz (2 ms)
./vxi11_cmd $PULSER "TRIG:SEQ:TIM 2e-3"
