
import time

import serial

#from hameg_trb import *

device = '/dev/ttyUSB_HAMEG_LV'
baudrate = 9600


def send_cmd(cmd,**kwargs):
  timeout = float(kwargs.get("timeout",0.2))

  with serial.Serial(device, baudrate, timeout=timeout) as ser:
    ser.write(str.encode(cmd)+b"\r\n")
    line = ser.readline().decode()
    ser.close()
    line = line.replace("\r","")
    line = line.replace("\n","")
    return line

def identify():
  return send_cmd("*IDN?")

def all_off():
  send_cmd("OUTPUT:GENERAL OFF")

def all_on():
  send_cmd("OUTPUT:GENERAL ON")

def get_volt(channel):
  return float(send_cmd("INST OUT{:d}\nMEAS:VOLT?".format(channel)))

def set_volt(channel,volt):
  send_cmd("INST OUT{:d}\nVOLT {:3.3f}".format(channel,volt))

def set_curr(channel,curr):
  send_cmd("INST OUT{:d}\nCURR {:3.3f}".format(channel,curr))

def get_curr(channel):
  return float(send_cmd("INST OUT{:d}\nMEAS:CURR?".format(channel)))

def get_state(channel):
  return int(send_cmd("INST OUT{:d}\nOUTP:STATE?".format(channel)))

def set_state(channel,state):
  send_cmd("INST OUT{:d}\nOUTP:STATE {:d}".format(channel,state))

def report():
  print("device: {:s}".format(device))
  for i in range(1,5):
    print("volt {:f} curr {:f} state {:d}".format( get_volt(i), get_curr(i), get_state(i))) 
    
    
    
from IPython.display import display, Markdown, clear_output
import ipywidgets as widgets


def OnOffButton(ch=1):
    button = widgets.Button(description='CH'+str(ch)+' ON')
    button2 = widgets.Button(description='CH'+str(ch)+' OFF')


    def on_button_clicked(_):
          # "linking function with output"
          with out:
              # what happens when we press the button
              clear_output()
              
              set_state(ch,1) 
              print('channel {:d} ON'.format(ch))
              #report()
    def off_button_clicked(_):
          # "linking function with output"
          with out:
              # what happens when we press the button
              clear_output()
              
              set_state(ch,0) 
              print('channel {:d} OFF'.format(ch))
             #report()
    # linking button and function together using a button's method
    button.on_click(on_button_clicked)
    button2.on_click(off_button_clicked)



    out = widgets.Output()

    # displaying button and its output together
    
    return(widgets.VBox([button,button2,out]))