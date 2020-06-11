
import os
import numpy as np
import re
from time import sleep


def trbcmd_write(TDC,register,data):
  os.system("trbcmd w {:s} 0x{:x} 0x{:x}".format(TDC,register,data))
  #print("trbcmd w {:s} 0x{:x} 0x{:x}".format(TDC,register,data))

def padiwa_thresh(TDC,chan,thresh):
  #print("PERL5LIB=/daqtools/perllibs /daqtools/tools/padiwa.pl {:s} 0 pwm {:d} 0x{:x}".format(TDC,chan,thresh))
  os.system("PERL5LIB=/daqtools/perllibs /daqtools/tools/padiwa.pl {:s} 0 pwm {:d} 0x{:x}".format(TDC,chan,thresh))
    


def read_memory(TDC,register,size):
  ### TDC is string, register and size are int
  mode = 0
  answer = os.popen("trbcmd rm {:s} {:d} {:d} {:d}".format(TDC,register,size,mode)).read()
  line_no = 0
  return_dict = {}
  for line in answer.split("\n"):
    if line_no > 0 and line_no <= size:
      line_split = re.split("\s+",line)
      return_dict[int(line_split[0],16)] = int(line_split[1],16)
    line_no+=1

  return return_dict

def read_scalers(TDC,channels):
  first_chan = channels[0]
  last_chan = channels[len(channels)-1]
  memory_size = last_chan-first_chan +1
  
  first_register = first_chan + 0xc001
  values = read_memory(TDC,first_register,memory_size)
  return_vals = [0] * len(channels)
  index = 0
  for ch in channels:
    # mask out first bit, because it is the input state
    return_vals[index] = values[ch + 0xc001] & 0x7fffffff
    index += 1

  return return_vals

def read_ch_state(TDC,channels):

  first_chan = channels[0]
  last_chan = channels[len(channels)-1]
  memory_size = last_chan-first_chan +1
  
  first_register = first_chan + 0xc001
  values = read_memory(TDC,first_register,memory_size)
  return_vals = [0] * len(channels)
  index = 0
  for ch in channels:
    # only take first bit, because it is the input state
    return_vals[index] = (values[ch + 0xc001] & 0x80000000)>>31
    index += 1

  return return_vals
  
def scaler_rate(TDC,channels,time):
  a = np.array(read_scalers(TDC,channels))
  sleep(time)
  b = np.array(read_scalers(TDC,channels))
  diff = b-a
  ## add overflow
  diff += (diff < 0)*(2**31)
  return diff.tolist()

def enable_channels(TDC,channels):
  mask = 0;
  for chan in channels:
    mask += 1<<chan
  upper_mask = (mask & 0xFFFFFFFF00000000)>>32
  lower_mask = mask & 0x00000000FFFFFFFF
  os.system("trbcmd setbit {:s} 0xc802 {:d}".format(TDC,lower_mask))
  os.system("trbcmd setbit {:s} 0xc803 {:d}".format(TDC,upper_mask))


def disable_channels(TDC,channels):
  mask = 0;
  for chan in channels:
    mask += 1<<chan
  upper_mask = (mask & 0xFFFFFFFF00000000)>>32
  lower_mask = mask & 0x00000000FFFFFFFF
  os.system("trbcmd clearbit {:s} 0xc802 {:d}".format(TDC,lower_mask))
  os.system("trbcmd clearbit {:s} 0xc803 {:d}".format(TDC,upper_mask))


