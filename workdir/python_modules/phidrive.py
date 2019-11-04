import re

import time

import serial

device = '/dev/ttyUSB_phidrive'
baudrate = 115200


def send_cmd(cmd,**kwargs):
  timeout = float(kwargs.get("timeout",4))

  with serial.Serial(device, baudrate, timeout=timeout) as ser:
    ser.write(str.encode(cmd)+b"\r\n")
    line = ser.readline().decode()
    ser.close()
    line = line.replace("\r","")
    line = line.replace("\n","")
    return line 

def read_line(**kwargs):
  timeout = float(kwargs.get("timeout",4))
  with serial.Serial(device, baudrate, timeout=timeout) as ser:
    line = ser.readline().decode()
    ser.close()
    line = line.replace("\r","")
    line = line.replace("\n","")
    return line 

def set_angle(deg):
  send_cmd(str(deg))
  time.sleep(4)
  cur_angle = get_angle()
  if deg == cur_angle:
    print ("okay, pos = {:f} deg".format(cur_angle))

def get_angle():
  return float(read_line().replace("pos degree ",""))