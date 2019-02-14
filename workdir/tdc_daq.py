
import os
from ROOT import TFile
import numpy as np
import json
import pasttrec_ctrl as ptc
import db


use_gausfit=0


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

