#!/usr/bin/env python

import os
import numpy as np
import json
import pasttrec_ctrl as ptc
import db
import tdc_daq






no_events=1000


### find board name of first TDC, first connector ###
#board_name = db.find_board_by_tdc_connector("0x0350",1)["name"]
#print "we are calibrating baselines for board "+board_name


#############   board name is the only thing that needs to be defined here, everythig else is loaded from db ################


def baseline_calib_by_noise(board_name):

  x, matrix = baseline_noise_scan(board_name)

  import matplotlib.pyplot as plt
  data = np.array(matrix)
  #plt.imshow(np.log(data))
  #plt.show()
  #plt.savefig("tmp.png")
  #os.system("display tmp.png")

  baselines = np.zeros(16)

  for ch in range(0,16):
    vals = data[:,ch]
    mean = float(np.dot(vals,x))/float(np.sum(vals))
    max  = x[np.argmax(vals)]
    baselines[ch] = mean
    #baselines[ch] = max

  db.update_calib_json_by_name(board_name,{"baselines": np.round(baselines).tolist() })
  ptc.init_active_boards()

  return baselines
    

def baseline_noise_scan(board_name):
  
  
  board_info = db.find_board_by_name(board_name)
  channels   = board_info["channels"] # zero based 
  TDC        = board_info["tdc_addr"]
  connector  = board_info["tdc_connector"]

  db.enable_board(board_name)
  ptc.init_active_boards()

  scan_time = 0.2
  
  ptc.set_threshold_for_board(TDC,connector,0)
  
  result_matrix = []
  x = range(-15,16)

  for i in x:
    ptc.set_all_baselines(TDC,channels, [i]*len(channels) )
    rates = tdc_daq.scaler_rate(TDC,channels,scan_time)
    result_matrix.append(rates)


  return (x, result_matrix)
  





def baseline_calib(board_name):
  
  channels   = db.find_board_by_name(board_name)["channels"] # zero based 
  TDC        = db.find_board_by_name(board_name)["tdc_addr"]

  db.enable_board(board_name)
  tdc_daq.enable_tdc_channels_of_active_boards()
  ptc.init_active_boards()
  
  
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
  
  
  
  
