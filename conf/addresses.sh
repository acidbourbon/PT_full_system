#!/bin/bash


#trbcmd s 0x7100000390255228  0x00 0x0350
#trbcmd s 0x8c0000039025fa28  0x01 0x0351
#trbcmd s 0xb00000039053e328  0x02 0x0352
#trbcmd s 0x790000039053dc28  0x03 0x0353
#trbcmd s 0x920000039053d928  0x05 0xc035

#trbcmd s 0x2b0000070f304f28  0x00 0x1500
#trbcmd s 0x180000070f306828  0x01 0x1501
#trbcmd s 0xc20000070f305928  0x02 0x1502
#trbcmd s 0x720000070f304c28  0x03 0x1503
#trbcmd s 0x290000070f305c28  0x05 0x8150

trbcmd s 0x610000050dec4328 1 0xc001
trbcmd s 0x3c00000a63104328 1 0x1000

echo "FPGAs after addressing"
trbcmd i 0xffff
