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
#print( "we are calibrating baselines for board "+board_name )


#############   board name is the only thing that needs to be defined here, everythig else is loaded from db ################

def char_noise_by_thresh_scan(board_name,**kwargs):

  ### kwargs is passed through to read/write calib files
  ### use baseline_calib_by_noise(board_name, dummy_calib=True) for test/dry run
  ### dummy_calib = kwargs.get("dummy_calib",False)


  x, matrix = threshold_noise_scan(board_name)

  data = np.array(matrix)

  baselines = np.zeros(16)
  baseline_stddev = np.zeros(16)

  for ch in range(0,16):
    vals = data[:,ch]
    sum  = float(np.sum(vals))
    mean = 0
    stddev  = -1
    if (sum > 0):
      weights = vals/float(sum)
      mean    = np.dot(weights,x)
      stddev    = np.sqrt(np.dot(weights,np.power(x-mean,2)))
    max  = x[np.argmax(vals)]
    baselines[ch] = mean
    baseline_stddev[ch] = stddev

  db.update_calib_json_by_name(board_name,{
    "tsbl_stddev"      : baseline_stddev.tolist(),
    "tsbl_mean"        : baselines.tolist(),
    "tsbl_range"       : x,
    "tsbl_scan_raw"    : np.transpose(data).tolist(),
  },**kwargs)
  ptc.init_board_by_name(board_name)

  return baselines

def baseline_calib_by_noise(board_name,**kwargs):

  ### kwargs is passed through to read/write calib files
  ### use baseline_calib_by_noise(board_name, dummy_calib=True) for test/dry run
  ### dummy_calib = kwargs.get("dummy_calib",False)

  individual = kwargs.get("individual",False)
  baseline_inactive = kwargs.get("baseline_inactive",[-15]*16)
  x = []
  matrix = []
  if individual:
    x, matrix = individual_channel_baseline_noise_scan(board_name,baseline_inactive)
  else:
    x, matrix = baseline_noise_scan(board_name)

  import matplotlib.pyplot as plt
  data = np.array(matrix)
  #plt.imshow(np.log(data))
  #plt.show()
  #plt.savefig("tmp.png")
  #os.system("display tmp.png")

  baselines = np.zeros(16)
  baseline_stddev = np.zeros(16)
  ch_error = np.zeros(16)

  max_baseline_stddev = 5
  global_settings = db.get_global_settings()
  if "max_baseline_stddev" in global_settings:
    max_baseline_stddev = global_settings["max_baseline_stddev"]

  for ch in range(0,16):
    vals = data[:,ch]
    sum  = float(np.sum(vals))
    mean = 0
    stddev  = -1
    if (sum > 0):
      weights = vals/float(sum)
      mean    = np.dot(weights,x)
      stddev    = np.sqrt(np.dot(weights,np.power(x-mean,2)))
    else:
      ch_error[ch] = 1
    max  = x[np.argmax(vals)]
    baselines[ch] = mean
    baseline_stddev[ch] = stddev
    if stddev >  max_baseline_stddev: 
      ch_error[ch] = 1
    #baselines[ch] = max

  db.update_calib_json_by_name(board_name,{
    "baselines"      : np.round(baselines).tolist(),
    "baseline_stddev"      : baseline_stddev.tolist(),
    "baseline_mean"  : baselines.tolist(),
    "bl_range"       : x,
    "noise_scan_raw" : np.transpose(data).tolist(),
    "ch_error"       : ch_error.tolist()
  },**kwargs)
  ptc.init_board_by_name(board_name)

  return baselines
 
def set_baselines_individual(board_name,baselines):    

  board_info = db.find_board_by_name(board_name)
  channels   = board_info["channels"] # zero based 
  TDC        = board_info["tdc_addr"]
  db.enable_board(board_name)
  ptc.set_all_baselines(TDC,channels,baselines)
  # do not perform init of boards afterwards, because this loads default baselines from calib json file / database
  #ptc.init_board_by_name(board_name)
    
  return 

def threshold_noise_scan(board_name):
  
  board_info = db.find_board_by_name(board_name)
  channels   = board_info["channels"] # zero based 
  TDC        = board_info["tdc_addr"]
  connector  = board_info["tdc_connector"]
  
  if TDC  == "0xeeef":
        return 0
    
  db.enable_board(board_name)
  #ptc.init_active_boards()
  #ptc.init_board_by_name(board_name)

  scan_time = 0.2
  x = list(range(0,32)) #default scan range 

  global_settings = db.get_global_settings()
  if "threshold_noise_scan_limit" in global_settings:
    threshold_noise_scan_limit = global_settings["threshold_noise_scan_limit"]
    x = list(range(0,threshold_noise_scan_limit))

  ## set baselines to maximum, so we start scanning below the baseline
  ## and hopefully capture the full noise
    
    #CW 7.4. deeactivated  moving baselinfe for this scan, 
     #as using individual baseline and do only threshold scan provides better comparison between diffent boards
  #ptc.set_all_baselines(TDC,channels, [15]*len(channels) )
  
  result_matrix = []

  for i in x:
    #print( "threshold scan of board "+board_name )
    ptc.set_threshold_for_board(TDC,connector,i)
    rates = tdc_daq.scaler_rate(TDC,channels,scan_time)
    #print( "rates" )
    #print( rates )
    result_matrix.append(rates)

  return (x, result_matrix)

def baseline_noise_scan(board_name):
  
  
  board_info = db.find_board_by_name(board_name)
  channels   = board_info["channels"] # zero based 
  TDC        = board_info["tdc_addr"]
  connector  = board_info["tdc_connector"]

  db.enable_board(board_name)
  #ptc.init_active_boards()
  #ptc.init_board_by_name(board_name)

  scan_time = 0.2
  
  ptc.set_threshold_for_board(TDC,connector,0)
  
  result_matrix = []
  x = list(range(-15,17))
  #ptc.init_boards_by_name([board_name], 10, 4)  
  for i in x:
   # print( "threshold scan of board "+board_name )
    ptc.set_all_baselines(TDC,channels, [i]*len(channels) )
    rates = tdc_daq.scaler_rate(TDC,channels,scan_time)
    #print( "rates" )
    #print( rates )
    result_matrix.append(rates)


  return (x, result_matrix)

def individual_channel_baseline_noise_scan(board_name,baseline_inactive=[-15]*16):
  
  
  board_info = db.find_board_by_name(board_name)
  channels   = board_info["channels"] # zero based 
  TDC        = board_info["tdc_addr"]
  connector  = board_info["tdc_connector"]

  db.enable_board(board_name)
  #ptc.init_active_boards()
  #ptc.init_board_by_name(board_name)

  scan_time = 0.2
  
  ptc.set_threshold_for_board(TDC,connector,0)
  
  result_matrix = []
  x = list(range(-15,17))

  for i in x:
    #print( "threshold scan of board "+board_name )
    rates = []
    #print( "setting baseline "+str(i) )
    for ch in range(0,16):
      #print( "probing channel "+str(ch) )
      ptc.set_all_baselines(TDC,channels,baseline_inactive)
      ptc.set_baseline(TDC,channels[ch],i)
      ch_rate = tdc_daq.scaler_rate(TDC,channels,scan_time)[ch]
      rates.append(ch_rate)

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
  
  print( "TDC" )
  print( TDC )
  print( "channels" )
  print( channels )
  print( "no_events" )
  print( no_events )
  
  
  tot_means = tdc_daq.get_tot(TDC,channels,no_events)
  
  print( "tot means:" )
  print( tot_means )
  
  
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
    
    print( "get new tot values" )
    tot_means = tdc_daq.get_tot(TDC,channels,no_events)
    print( tot_means )
    print( "deltas to target tot" )
    print( tot_means - target_tot )
    print( "deltas to target tot in percent" )
    print( (tot_means - target_tot)/target_tot*100. )
    print( "final baselines" )
    print( np.floor(baselines) )
  
  print( "save baselines in calib file" )
  
  db.update_calib_json_by_name(board_name,{"baselines": np.floor(baselines).tolist() })
  
  
  
  
