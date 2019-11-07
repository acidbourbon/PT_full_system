def take_data(**kwargs):
    import os
    events  = int(kwargs.get("events",0))
    time = float(kwargs.get("time",0))
    os.system("rm /workdir/*.root")
    if( time > 0 ):
      os.system("cd /workdir; ./take_data_n_sec.sh {:f}".format(time))
    else:
      os.system("cd /workdir; ./take_data_n_evt.sh {:d}".format(events))
    #os.system("cd /workdir; root -b -l unify.C -q")


def take_raw_data(**kwargs):
    import os
    time = float(kwargs.get("time",10))
    label = kwargs.get("label","")
    os.system("cd /workdir; ./take_raw_data_n_sec.sh {:f} {:s}".format(time,label))



    

def trigger_scinti():
  import os
  os.system("cd /conf; ./trigger_scinti.sh")
    
def trigger_ufsd():
  import os
  os.system("cd /conf; ./trigger_ufsd.sh")
    
def wait_for_spill():
 # untested
 import scaler
 trigger_rate_threshold = 4000
 poll_acq_time = 1
 ### wait for spill start
 trig_chan = 30
 while True:
   curr_rates = scalers.scaler_rate("0x0351",[trig_chan],poll_acq_time)
   scint_rate = curr_rates[0]
   if scint_rate > trigger_rate_threshold*poll_acq_time:
     print("## spill start ##")
     break
   else:
     print(".", end=" ")
        
#    ### wait for spill break
#    while True:
#      curr_rates = scalers.scaler_rate("0x0351",[dut_chan,trig_chan],poll_acq_time)
#      scint_rate = curr_rates[1]
#      if scint_rate < trigger_rate_threshold*poll_acq_time:
#        print("## spill break ##")
#        break
#      else:
#        print(":", end=" ")