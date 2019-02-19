#!/usr/bin/env python

import os
import numpy as np
import json
import pasttrec_ctrl as ptc
import db
import tdc_daq






no_events=1000


### find board name of first TDC, first connector ###
board_name = db.find_board_by_tdc_connector("0x0350",1)["name"]
print "we are calibrating baselines for board "+board_name


#############   board name is the only thing that needs to be defined here, everythig else is loaded from db ################


channels   = db.find_board_by_name(board_name)["channels"] # zero based 
TDC        = db.find_board_by_name(board_name)["tdc_addr"]


baselines = np.zeros(len(channels))

ptc.set_all_baselines(TDC,channels,baselines)

print "TDC"
print TDC
print "channels"
print channels
print "no_events"
print no_events


tot_means = tdc_daq.get_tot(TDC,channels,no_events)

print "tot means:"
print tot_means


target_tot = tot_means.mean()
print("target tot: {:f}".format(target_tot))


print("start auto correction procedure")

for step_width in [8,4,4,3,2,1,1,0.5,0.5,0.5,0.5,0.5]:
  print("step width: {:02f}".format(step_width))
  
  for index in range(0,len(channels)):
    if (tot_means[index] < target_tot):
      baselines[index]+=step_width
    else:
      baselines[index]-=step_width
    baselines[index]=np.max([baselines[index],-15])
    baselines[index]=np.min([baselines[index],15])
      
  ptc.set_all_baselines(TDC,channels,baselines)
  
  print "get new tot values"
  tot_means = tdc_daq.get_tot(TDC,channels,no_events)
  print tot_means
  print "deltas to target tot"
  print tot_means - target_tot
  print "deltas to target tot in percent"
  print (tot_means - target_tot)/target_tot*100.
  print "final baselines"
  print np.floor(baselines)

print "save baselines in calib file"

db.update_calib_json_by_name(board_name,{"baselines": np.floor(baselines).tolist() })




