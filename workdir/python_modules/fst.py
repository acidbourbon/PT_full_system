def take_data(**kwargs):
    import os
    events  = int(kwargs.get("events",0))
    time = float(kwargs.get("time",0))
    os.system("rm /workdir/*.root")
    if( time > 0 ):
      os.system("cd /workdir; ./take_data_n_sec.sh {:f}".format(time))
    else:
      os.system("cd /workdir; ./take_data_n_evt.sh {:d}".format(events))
    os.system("cd /workdir; root -b -l unify.C -q")
