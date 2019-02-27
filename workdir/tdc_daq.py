
import os
from ROOT import TFile
import numpy as np
import db

use_gausfit=0


def enable_channels(TDC,channels):
  mask = 0;
  for chan in channels:
    mask += 1<<chan
  os.system("trbcmd setbit {:s} 0xc802 {:d}".format(TDC,mask))


def disable_channels(TDC,channels):
  mask = 0;
  for chan in channels:
    mask += 1<<chan
  os.system("trbcmd clearbit {:s} 0xc802 {:d}".format(TDC,mask))


def enable_tdc_channels_of_active_boards():
  ### disable all daq channels of listed TDCs
  for tdc_addr in db.tdc_list():
    if tdc_addr[0:2].lower() == "0x":
      disable_channels(tdc_addr,range(0,32))
  
  for board_name in db.active_board_list():
    board_info = db.find_board_by_name(board_name)
    channels = board_info["channels"]
    tdc_addr = board_info["tdc_addr"]
    if tdc_addr[0:2].lower() == "0x":
      enable_channels(tdc_addr,channels)
  return




def record_tree_data(no_events):
  dummy=os.popen("rm *.root; tree_out=true go4analysis -number 1000 -stream localhost:6790; root -b -l unify.C -q".format(no_events)).read()
  return



def get_t1_tot(tdc_addr,channels):
  ## run record_tree_data() first ##
  
  f = TFile("joint_tree.root")

  t1 = np.zeros(len(channels))
  tot = np.zeros(len(channels))

  t1_meta  = f.Get(str(tdc_addr)+"_t1_meta")
  tot_meta = f.Get(str(tdc_addr)+"_tot_meta")
  
  index=0
  for i in channels:
    t1[index]  = t1_meta.ProjectionX("dummy",i+1,i+1).GetMean()
    tot[index] = tot_meta.ProjectionX("dummy",i+1,i+1).GetMean()
    index += 1

  return (t1.tolist(), tot.tolist())

def calib_t1_offsets(tdc_addr,channels):
  record_tree_data(1000)
  t1, tot = get_t1_tot(tdc_addr,channels)
  tdc_json = db.get_tdc_json(tdc_addr)
  index=0
  for ch in channels:
    tdc_json["t1_offset"][ch] = t1[index]
    index+=1
  db.write_tdc_json(tdc_addr,tdc_json)

def calib_t1_offsets_of_board(board_name):
  ## run record_tree_data() first ##
  board_info = db.find_board_by_name(board_name)
  calib_t1_offsets(board_info["tdc_addr"],board_info["channels"])

def get_t1_tot_of_board(board_name):
  ## run record_tree_data() first ##
  board_info = db.find_board_by_name(board_name)
  return get_t1_tot(board_info["tdc_addr"],board_info["channels"])

def get_tot(TDC, channels, no_events):
  
  os.system("rm Go4AutoSave.root")
  dummy=os.popen("go4analysis -number {:d} -stream localhost:6790".format(no_events)).read()
  
  f = TFile("Go4AutoSave.root")
  tot_means = np.zeros(len(channels))
  
  my_tdc = str(TDC).replace("0x","")
  
  print "my tdc: "+my_tdc
  print "channels: "
  print channels

  index=0
  for i in channels:
    chan = "{:02d}".format(i+1)
    hist = f.Get("Histograms/Sec_"+my_tdc+"/Sec_"+my_tdc+"_Ch"+chan+"_tot")
    tot_mean = hist.GetMean()
    if use_gausfit :
      hist.Fit("gaus","WWq")
      tot_mean = hist.GetFunction("gaus").GetParameter(1)
    
    tot_means[index] = tot_mean
    index+=1
    #print("chan "+chan+"  tot mean: "+str(tot_mean))
    


  return tot_means

