import re

import time

import serial

device = '/dev/ttyUSB_micos_eco'


def send_cmd(cmd,**kwargs):
  timeout = float(kwargs.get("timeout",1))

  with serial.Serial(device, 57600, timeout=timeout) as ser:
    ser.write(str.encode(cmd)+b"\r\n")
    line = ser.readline().decode()
    ser.close()
    line.replace("\r","")
    line.replace("\n","")
    return line 

def pos():
  pattern =  re.compile("([0-9E+\-.]+)\s+([0-9E+\-.]+)\s+([0-9E+\-.]+)")
  answer = send_cmd("pos")
  match = re.search(pattern, answer)
  if match:
    return (float(match.groups()[0]),float(match.groups()[1]),float(match.groups()[2]))

def move(**kwargs):
  current_x , current_y, current_z = pos()
  
  x = float(kwargs.get("x",current_x))
  y = float(kwargs.get("y",current_y))
  z = float(kwargs.get("z",current_z))

  send_cmd("{:f} {:f} {:f} move".format(x,y,z))
  time.sleep(0.5)
  while( pos() != ( float("{:5.5f}".format(x)), float("{:5.5f}".format(y)), float("{:5.5f}".format(z)) ) ):
    print(pos())
    time.sleep(0.5)
  print(pos())
  print("done")


#enable axis 1,2
send_cmd("1 1 setaxis")
send_cmd("1 2 setaxis")