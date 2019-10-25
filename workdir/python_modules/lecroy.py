#!/usr/bin/env python3
 
import numpy as np
#import vxi11
from numpy import pi
import array
import time
 
# change the IP address to your lecroy.ument's IP
#lecroy.= vxi11.Instrument('TCPIP0::140.181.69.117::INSTR')
#lecroy.= vxi11.Instrument('USB0::0x05ff::0x1023::2805N57162::INSTR')
#print(lecroy.ask('*IDN?'))

#import visa
#rm = visa.ResourceManager()

import vxi11

#lecroy= rm.open_resource('USB0::0x05ff::0x1023::2805N57162::INSTR')

#lecroy = rm.open_resource('TCPIP0::192.168.43.20::INSTR') ## if you use this, set lofirst to False

lecroy = vxi11.Instrument('TCPIP0::192.168.43.20::INSTR')

ovrride_lofirst = False ## needed if you use lxi
ovrride_lofirst_val = False ## needed if you use lxi

lecroy.timeout = 2000
lecroy.clear()
lecroy.chunk_size = 102400


print(lecroy.ask("*IDN?"))


def prefix_number(number):
  nstr = str(number)
  if number < 1e-6:
    nstr = str(number*1e9)+"N"
  elif number < 1e-3:
    nstr = str(number*1e6)+"U"
  elif number < 1e-0:
    nstr = str(number*1e3)+"M"
  return nstr
    
def next_bigger_125_number(x):
  a = x
  e = 1
  if(x < 1e-6):
    a = x/1e-9
    e = 1e-9
  elif( x < 1e-3):
    a = x/1e-6
    e = 1e-6
  
  if a <= 1:
    a = 1
  elif a <= 2:
    a = 2
  elif a <= 5:
    a = 5
  elif a <= 10:
    a = 10
  elif a <= 20:
    a = 20
  elif a <= 50:
    a = 50
  elif a <= 100:
    a = 100
  elif a <= 200:
    a = 200
  elif a <= 500:
    a = 500
  elif a <= 1000:
    a = 1000
  
  return a*e



def clear_all():
  lecroy.write(r"""vbs 'app.measure.clearall ' """)
  lecroy.write(r"""vbs 'app.measure.clearsweeps ' """)


def setup_measurement(meas_no,meas_source,meas_type):
  lecroy.write(r"""vbs 'app.measure.showmeasure = true ' """)
  lecroy.write(r"""vbs 'app.measure.statson = true ' """)
  lecroy.write(r"""vbs 'app.measure."""+meas_no+r""".view = true ' """)
  lecroy.write(r"""vbs 'app.measure."""+meas_no+'.paramengine = "'  + meas_type +   r"""" ' """)
  lecroy.write(r"""vbs 'app.measure."""+meas_no+'.source1 = "'      + meas_source + r"""" ' """)






def measure_statistics(sources, n):
  first =  True
  
  return_dict = {}
  
  for source in sources:
    return_dict[source] = np.zeros(n)
  
  
  for j in range(0,n):
    if first:
      lecroy.write(r"""vbs 'app.ClearSweeps ' """)
      
    r = lecroy.ask(r"""vbs? 'return=app.acquisition.acquire( 0.1 , True )' """)
    r = lecroy.ask(r"""vbs? 'return=app.WaitUntilIdle(5)' """)
    if r==0:
      print ("Time out from WaitUntilIdle, return = {0}".format(r))
      
    for source in sources:
      return_dict[source][j] = read_measure(source)

  return return_dict

def read_measure(source): # p1 p2 ...
  answer = lecroy.ask(r"""vbs? 'return=app.measure.""" +source.lower() + r""".out.result.value' """)
  if 'No Data Available' in answer:
    return np.nan
  else:
    return float(answer)

def trigger_n_times(n,**kwargs):
  clear_sweeps = kwargs.get("clear_sweeps",True)
  # stop acquisition
  lecroy.write(r"""vbs 'app.acquisition.triggermode = "stopped" ' """)

  time.sleep(0.1)

  # clear averaging
  if clear_sweeps:
    lecroy.write(r"""vbs 'app.ClearSweeps ' """)
    
  for i in range(0,n):
    r = lecroy.ask(r"""vbs? 'return=app.acquisition.acquire( 0.1 , True )' """)
    r = lecroy.ask(r"""vbs? 'return=app.WaitUntilIdle(5)' """)
    if r==0:
      print ("Time out from WaitUntilIdle, return = {0}".format(r))
      
def set_tdiv(tdiv):      
  lecroy.write("TDIV {:e}".format(tdiv))

def set_trigger_delay(trdl):
  lecroy.write("TRDL {:e}".format(trdl))
  
def set_vdiv(source,vdiv):
  lecroy.write("{:s}:VDIV {:e}".format(source,vdiv))
  
def set_voffset(source,offset):
  lecroy.write("{:s}:OFFSET {:e}".format(source,offset))
  
def set_trig_source(source):
  lecroy.write("TRIG_SELECT edge,SR,{:s} ".format(source))

def capture_waveforms(sources,**kwargs):
  
  
  average = kwargs.get("average",1)

  if "vdiv" in kwargs:
    vdivs = kwargs.get("vdiv",{})
    for source in sources:
      if source in vdivs:
        vdiv   = vdivs[source]
        set_vdiv(source,vdiv)

  if "tdiv" in kwargs:
    tdiv = kwargs.get("tdiv",1)
    set_tdiv(tdiv)

  if "trdl" in kwargs:
    trdl = kwargs.get("trdl",0)
    set_trigger_delay(trdl)
    
  n = kwargs.get("trigger_n_times",1)

  ### set default settings
  #lecroy.write(r"""vbs 'app.settodefaultsetup' """)

  
  avg_runs = 0
  
  x = None
  y = {}
  
  for i in range(0,average):
    trigger_n_times(n,**kwargs)
    for source in sources:
      x,y_ = transfer_waveform(source,**kwargs)
      if avg_runs == 0:
        y[source] = y_
      else:
        y[source] += y_
    avg_runs += 1
    
  for source in sources:
    y[source] /= float(average)
  
    
  return x,y


def transfer_waveform(source,**kwargs):
  
  # example: acquire_waveform("C1")
  
  use_vertical_offset = kwargs.get("use_vertical_offset",False)
  
  lecroy.write("COMM_HEADER OFF ")

  # set waveform format to 16 bit
  lecroy.write("COMM_FORMAT DEF9,WORD,BIN ")
  # set waveform format to 8 bit
  #lecroy.write("COMM_FORMAT DEF9,BYTE,BIN ")




  WAVEDESC_STR = lecroy.ask(r"""{:s}:INSPECT? "WAVEDESC" """.format(source))
  #print( "WAVEDESC = {0}".format(WAVEDESC_STR))

  lecroy.write("{:s}:WAVEFORM? ".format(source) )
  WAVEFORM = lecroy.read_raw( )


  wavedesc = {}
  for line in WAVEDESC_STR.split("\r\n"):
    key_val = line.replace(" ","").replace("\u0000","").split(":") 
    if len(key_val) == 2:
      wavedesc[key_val[0]] = key_val[1]

  word_length = 1
  if wavedesc["COMM_TYPE"]=="word":
    word_length = 2

  samples = int(wavedesc["WAVE_ARRAY_COUNT"]) -3
  
  vertical_offset = 0
  if use_vertical_offset:
    vertical_offset = float(wavedesc["VERTICAL_OFFSET"])
  
  horiz_offset = float(wavedesc["HORIZ_OFFSET"])
  vertical_gain = float(wavedesc["VERTICAL_GAIN"])
  lofirst = (wavedesc["COMM_ORDER"] == "LOFIRST")
  if ovrride_lofirst:
    lofirst = ovrride_lofirst_val
  trace_y = np.zeros(samples)



  for i in range(0,samples):
    val = 0
    if word_length == 2:
      val1 = WAVEFORM[-samples*2+2*i]
      val2 = WAVEFORM[-samples*2+2*i+1]
      if lofirst:
        val = (val1<<8) + val2
      else:
        val = (val2<<8) + val1
      val = int.from_bytes(val.to_bytes(length=2,byteorder="little"),byteorder="little",signed=True)
    else:
      val = WAVEFORM[-samples+i]
      val = int.from_bytes(val.to_bytes(length=1,byteorder="little"),byteorder="little",signed=True)
    trace_y[i] = val* vertical_gain + vertical_offset
    

  trace_x = np.linspace(horiz_offset,horiz_offset+float(wavedesc["HORIZ_INTERVAL"])*samples,samples)

  return (trace_x, trace_y)
  #print("trace y length: {:d}".format(len(trace_y)))

  #COMM_TYPE = lecroy.ask(r"""COMM_TYPE? """)
  #print( "COMM_TYPE = {0}".format(COMM_TYPE))

  #print("word length: {:d}".format(word_length))

  #import json
  #print(json.dumps(wavedesc,sort_keys=True,indent=2))


## called if module is terminated
def __del__(self):
  print("goodbye lecroy scope")
  lecroy.close()
  rm.close()


