#!/bin/bash

trbcmd reload 0x0350
trbcmd reload 0x0351
trbcmd reload 0x0352
trbcmd reload 0x0353
trbcmd reload 0xc035 

sleep 4

./addresses.sh
