# CTS Configuration dump
#  generated:        2021-11-03 13:01
#  CTS Compile time: 2020-06-29 11:12
#
# trbcmd Dev.   Reg.   Value
trbcmd setbit 0xc035 0xa00c 0x80000000  # Disable all triggers
trbcmd w 0xc035 0xa008 0xffffffff  # cts_fsm_limits: ro=65535, td=65535
trbcmd w 0xc035 0xa009 0x00000001  # cts_readout_config: 
                            # channel_cnt=false, idle_dead_cnt=false, input_cnt=true
                            # timestamp=false, trg_cnt=false
trbcmd w 0xc035 0xa00c 0x80000014  # cts_throttle: enable=false, stop=false, threshold=20
trbcmd w 0xc035 0xa00d 0x00000001  # cts_eventbuilder: 
                            # cal_eb=0, mask=0000 0000 0000 0001, rr_interval=0
                            # use_cal_eb=false
trbcmd w 0xc035 0xa101 0xffff0008  # trg_channel_mask: edge=1111 1111 1111 1111, mask=0000 0000 0000 1000
trbcmd w 0xc035 0xa124 0x00000014  # trg_input_config0: delay=20, invert=false, override=off, spike_rej=0
trbcmd w 0xc035 0xa125 0x00000014  # trg_input_config1: delay=10, invert=false, override=off, spike_rej=0
trbcmd w 0xc035 0xa126 0x00000000  # trg_input_config2: delay=0, invert=false, override=off, spike_rej=0
trbcmd w 0xc035 0xa127 0x00000000  # trg_input_config3: delay=0, invert=false, override=off, spike_rej=0
trbcmd w 0xc035 0xa128 0x00000000  # trg_input_config4: delay=0, invert=false, override=off, spike_rej=0
trbcmd w 0xc035 0xa129 0x00000000  # trg_input_config5: delay=0, invert=false, override=off, spike_rej=0
trbcmd w 0xc035 0xa12a 0x00000000  # trg_input_config6: delay=0, invert=false, override=off, spike_rej=0
trbcmd w 0xc035 0xa12b 0x00000000  # trg_input_config7: delay=0, invert=false, override=off, spike_rej=0
trbcmd w 0xc035 0xa13e 0x00000000  # trg_coin_config0: 
                            # coin_mask=0000 0000, inhibit_mask=0000 0000
                            # window=0
trbcmd w 0xc035 0xa13f 0x00000001  # trg_coin_config1: 
                            # coin_mask=0000 0001, inhibit_mask=0000 0000
                            # window=0
trbcmd w 0xc035 0xa141 0x00000030  # trg_input_mux0: input=itc[10]
trbcmd w 0xc035 0xa142 0x00000028  # trg_input_mux1: input=itc[2]
trbcmd w 0xc035 0xa143 0x00000005  # trg_input_mux2: input=jeclin[1]
trbcmd w 0xc035 0xa144 0x00000006  # trg_input_mux3: input=jeclin[2]
trbcmd w 0xc035 0xa145 0x00000004  # trg_input_mux4: input=jeclin[0]
trbcmd w 0xc035 0xa146 0x00000000  # trg_input_mux5: input=extclk[0]
trbcmd w 0xc035 0xa147 0x00000001  # trg_input_mux6: input=extclk[1]
trbcmd w 0xc035 0xa148 0x00000002  # trg_input_mux7: input=trgext[2]
trbcmd w 0xc035 0xa14a 0x00000004  # trg_addon_output_mux0: input=itc[4]
trbcmd w 0xc035 0xa14b 0x00000005  # trg_addon_output_mux1: input=itc[5]
trbcmd w 0xc035 0xa14c 0x00000006  # trg_addon_output_mux2: input=itc[6]
trbcmd w 0xc035 0xa14d 0x00000007  # trg_addon_output_mux3: input=itc[7]
trbcmd w 0xc035 0xa14e 0x00000004  # trg_addon_output_mux4: input=itc[4]
trbcmd w 0xc035 0xa14f 0x00000002  # trg_addon_output_mux5: input=itc[2]
trbcmd w 0xc035 0xa150 0x00000000  # trg_addon_output_mux6: input=itc[0]
trbcmd w 0xc035 0xa151 0x00000000  # trg_addon_output_mux7: input=itc[0]
trbcmd w 0xc035 0xa153 0x00000002  # trg_periph_config0: mask=0000 0000 0000 0000 0010
trbcmd w 0xc035 0xa154 0x000fffff  # trg_periph_config1: mask=1111 1111 1111 1111 1111
trbcmd w 0xc035 0xa155 0x00000003  # trg_periph_config2: mask=0000 0000 0000 0000 0011
trbcmd w 0xc035 0xa156 0x00000000  # trg_periph_config3: mask=0000 0000 0000 0000 0000
trbcmd w 0xc035 0xa158 0x0001869f  # trg_pulser_config0: low_duration=99999
trbcmd w 0xc035 0xa15a 0x11111111  # trg_random_pulser_config0: threshold=286331153
trbcmd w 0xc035 0xa15c 0x1111111d  # _trg_trigger_types0: 
                            # type0=0xd_tdc_calibration_trigger, type1=0x1_physics_trigger
                            # type2=0x1_physics_trigger, type3=0x1_physics_trigger
                            # type4=0x1_physics_trigger, type5=0x1_physics_trigger
                            # type6=0x1_physics_trigger, type7=0x1_physics_trigger
trbcmd w 0xc035 0xa15d 0x11111111  # _trg_trigger_types1: 
                            # type10=0x1_physics_trigger, type11=0x1_physics_trigger
                            # type12=0x1_physics_trigger, type13=0x1_physics_trigger
                            # type14=0x1_physics_trigger, type15=0x1_physics_trigger
                            # type8=0x1_physics_trigger, type9=0x1_physics_trigger
trbcmd clearbit 0xc035 0xa00c 0x80000000  # Enable all triggers
