import serial

device = '/dev/ttyUSB_wallplugs'
baudrate = 115200


def send_cmd(cmd,**kwargs):
  timeout = float(kwargs.get("timeout",0.2))

  with serial.Serial(device, baudrate, timeout=timeout) as ser:
    ser.write(str.encode(cmd)+b"\r\n")
    line = ser.readline().decode()
    ser.close()
    line.replace("\r","")
    line.replace("\n","")
    return line 

def a_on():
   send_cmd("a on")

def a_off():
   send_cmd("a off")

def b_on():
   send_cmd("b on")

def b_off():
   send_cmd("b off")

def c_on():
   send_cmd("c on")

def c_off():
   send_cmd("c off")

def d_on():
   send_cmd("d on")

def d_off():
   send_cmd("d off")

def all_on():
    send_cmd("all on")

def all_off():
    send_cmd("all off")
