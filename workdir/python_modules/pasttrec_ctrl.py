
import os
from time import sleep

pasttrec_ctrl_dir="/workdir/python_modules/pasttrec_ctrl"

def set_baseline(TDC, conn,channel,val):

  chip = int(channel/8)
  chip_chan=channel%8
  os.system("cd "+pasttrec_ctrl_dir+"; TDC="+TDC+" CONN={:d} CHIP={:d} ./baseline {:d} {:d}".format(conn,chip, chip_chan ,val))

  return

def set_threshold(TDC,conn,chip,thresh):
  os.system("cd "+pasttrec_ctrl_dir+"; TDC="+TDC+" CONN={:d} CHIP={:d} ./threshold {:d}".format(conn,chip,thresh))

def set_threshold_for_board(TDC,conn,thresh):
  set_threshold(TDC,conn,0,thresh)
  set_threshold(TDC,conn,1,thresh)



def set_all_baselines( TDC, channels, values): # channels and values have to have same dimensions
  print("set baselines of the following channels")
  print( channels )
  print("to the following values")
  print( values )
  index=0
  for i in channels:
    set_baseline(TDC,i,int(values[index]))
    index+=1
    
  return

def init_chip(TDC,conn,chip,pktime,gain,thresh):
  
  if( pktime == 10 ):
    os.system("cd "+pasttrec_ctrl_dir+"; TDC="+TDC+" CONN={:d} CHIP={:d} ./spi blue_settings_pt10_g1_thr127".format(conn,chip))
  if( pktime == 15 ):
    os.system("cd "+pasttrec_ctrl_dir+"; TDC="+TDC+" CONN={:d} CHIP={:d} ./spi black_settings_pt15_g1_thr127".format(conn,chip))
  if( pktime == 20 ):
    os.system("cd "+pasttrec_ctrl_dir+"; TDC="+TDC+" CONN={:d} CHIP={:d} ./spi black_settings_pt20_g1_thr127".format(conn,chip))

  os.system("cd "+pasttrec_ctrl_dir+"; TDC="+TDC+" CONN={:d} CHIP={:d} pktime={:d} gain={:d} ./set_gain_pktime".format(conn,chip,pktime,gain))
  os.system("cd "+pasttrec_ctrl_dir+"; TDC="+TDC+" CONN={:d} CHIP={:d} ./threshold {:d}".format(conn,chip,thresh))
  
  
  return

def reset_board(TDC,conn):
  os.system("cd "+pasttrec_ctrl_dir+"; TDC="+TDC+" CONN={:d} ./reset ".format(conn))

def init_board(TDC,conn,pktime,gain,thresh):
  reset_board(TDC,conn)
  init_chip(TDC,conn,0,pktime,gain,thresh)
  init_chip(TDC,conn,1,pktime,gain,thresh)
  return
 
