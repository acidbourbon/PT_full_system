
import os

def set_baseline( TDC, channel,val):
  
  conn=int(channel/16)+1
  chip=int((channel%16)/8)
  chip_chan=channel%8

  os.system("cd pasttrec_ctrl; TDC="+TDC+" CONN={:d} CHIP={:d} ./baseline {:d} {:d}".format(conn,chip, chip_chan ,val))

  return

def set_all_baselines( TDC, channels, values): # channels and values have to have same dimensions
  print("set baselines of the following channels")
  print channels
  print("to the following values")
  print values
  index=0
  for i in channels:
    set_baseline(TDC,i,int(values[index]))
    index+=1
    
  return
