#!/usr/bin/env python

import os
from ROOT import TFile
import numpy as np
import json
#from pasttrec_ctrl import *
import pasttrec_ctrl as ptc

#print("Hallo Welt!")
#os.system("./tot_calib.sh Go4AutoSave.root -q > calib_out.txt")

use_gausfit=0


def get_tot( file, TDC, channels, no_events):
  
  os.system("rm Go4AutoSave.root")
  os.system("go4analysis -number {:d} -stream localhost:6790".format(no_events))
  
  f = TFile(file)
  tot_means = np.zeros(len(channels))
  
  index=0
  for i in channels:
    chan = "{:02d}".format(i+1)
    hist = f.Get("Histograms/Sec_"+TDC+"/Sec_"+TDC+"_Ch"+chan+"_tot")
    tot_mean = hist.GetMean()
    if use_gausfit :
      hist.Fit("gaus","WWq")
      tot_mean = hist.GetFunction("gaus").GetParameter(1)
    
    tot_means[index] = tot_mean
    index+=1
    #print("chan "+chan+"  tot mean: "+str(tot_mean))
    


  return tot_means



########## main script ##########

TDC="0350"
file="Go4AutoSave.root"
#channels=range(16,32) # zero based 
channels=range(0,16) # zero based 
no_events=1000
chip=0


baselines = np.zeros(len(channels))

ptc.set_all_baselines(TDC,channels,baselines)

#for i in range(0,16):
  #print("set zero baseline channel {:d}".format(i))
  #set_baseline(TDC,chip,i,0)
  

tot_means = get_tot(file,TDC,channels,no_events)

print "tot means:"
print tot_means

#print "tot means, all channels" 
#print tot_means
##print tot_means[1]

target_tot = tot_means.mean()
#target_tot=109

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
  tot_means = get_tot(file,TDC,channels,no_events)
  print tot_means
  print "deltas to target tot"
  print tot_means - target_tot
  print "deltas to target tot in percent"
  print (tot_means - target_tot)/target_tot*100.


#input()


