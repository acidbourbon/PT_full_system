#!/bin/bash

## display ch1 output voltage
./vxi11_cmd $PULSER "SOUR1:VOLT?"

## display internal trigger repetition rate
./vxi11_cmd $PULSER "TRIG:SEQ:TIM?"
