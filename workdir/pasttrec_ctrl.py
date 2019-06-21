
import os
import db
import tdc_daq
from time import sleep


def slow_control_test(board_name):
  
  scan_time = 0.2
  
  board_info = db.find_board_by_name(board_name)
  channels   = board_info["channels"] # zero based 
  TDC        = board_info["tdc_addr"]
  connector  = board_info["tdc_connector"]

  db.enable_board(board_name)
  init_board_by_name(board_name)

  
  print "slow control test of board "+board_name
  set_threshold_for_board(TDC,connector,0)
  rates_lo_thr = tdc_daq.scaler_rate(TDC,channels,scan_time)

  set_threshold_for_board(TDC,connector,127)
  rates_hi_thr = tdc_daq.scaler_rate(TDC,channels,scan_time)
  state_hi_thr = tdc_daq.read_ch_state(TDC,channels)
 
  print "rates low thr"
  print rates_lo_thr
  print "rates high thr"
  print rates_hi_thr
  print "state high thr"
  print state_hi_thr

  if state_hi_thr == [1]*len(channels) and rates_hi_thr == [0]*len(channels) and rates_lo_thr != [0]*len(channels):
    return 1
  else:
    return 0

def set_baseline( TDC, channel,val):

  chip = db.calc_chip_from_channel(channel)
  conn = db.calc_connector_from_channel(channel)
  chip_chan=channel%8
  os.system("cd pasttrec_ctrl; TDC="+TDC+" CONN={:d} CHIP={:d} ./baseline {:d} {:d}".format(conn,chip, chip_chan ,val))

  return

def set_threshold(TDC,conn,chip,thresh):
  os.system("cd pasttrec_ctrl; TDC="+TDC+" CONN={:d} CHIP={:d} ./threshold {:d}".format(conn,chip,thresh))

def set_threshold_for_board(TDC,conn,thresh):
  set_threshold(TDC,conn,0,thresh)
  set_threshold(TDC,conn,1,thresh)

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

def init_chip(TDC,conn,chip,pktime,gain,thresh):
  
  if( pktime == 10 ):
    os.system("cd pasttrec_ctrl; TDC="+TDC+" CONN={:d} CHIP={:d} ./spi blue_settings_pt10_g1_thr127".format(conn,chip))
  if( pktime == 15 ):
    os.system("cd pasttrec_ctrl; TDC="+TDC+" CONN={:d} CHIP={:d} ./spi black_settings_pt15_g1_thr127".format(conn,chip))
  if( pktime == 20 ):
    os.system("cd pasttrec_ctrl; TDC="+TDC+" CONN={:d} CHIP={:d} ./spi black_settings_pt20_g1_thr127".format(conn,chip))

  os.system("cd pasttrec_ctrl; TDC="+TDC+" CONN={:d} CHIP={:d} pktime={:d} gain={:d} ./set_gain_pktime".format(conn,chip,pktime,gain))
  os.system("cd pasttrec_ctrl; TDC="+TDC+" CONN={:d} CHIP={:d} ./threshold {:d}".format(conn,chip,thresh))
  board_info = db.find_board_by_tdc_connector(TDC,conn)
  board_name = board_info["name"] 
  board_channels = board_info["channels"] 
  calib = db.get_calib_json_by_name(board_name)
  if ("baselines" in calib):
    board_baselines = calib["baselines"]
    channels = board_channels[0:9]
    values   = board_baselines[0:9]
    if chip == 1:
      channels = board_channels[8:17]
      values   = board_baselines[8:17]
    set_all_baselines(TDC,channels,values)
  return

def reset_board_by_name(board_name):
  board_info = db.find_board_by_name(board_name)
  conn = board_info["tdc_connector"]
  tdc_addr = board_info["tdc_addr"]
  if tdc_addr[0:2].lower() == "0x":
    reset_board(tdc_addr,conn)

def reset_board(TDC,conn):
  os.system("cd pasttrec_ctrl; TDC="+TDC+" CONN={:d} ./reset ".format(conn))

def init_board(TDC,conn,pktime,gain,thresh):
  reset_board(TDC,conn)
  init_chip(TDC,conn,0,pktime,gain,thresh)
  init_chip(TDC,conn,1,pktime,gain,thresh)
  return
 

def slow_control_test_active_boards(): 
  test_results = {}
  for board_name in db.active_board_list():
    answer = slow_control_test(board_name)
    test_results[board_name] = answer

  print test_results
  return test_results

def init_active_boards():
  return init_boards_by_name(db.active_board_list())

def init_boards_by_name(board_list):
  
  setup     = db.get_setup_json()

  pktime    = setup["asic_settings"]["default"]["pktime"]
  gain      = setup["asic_settings"]["default"]["gain"]
  threshold = setup["asic_settings"]["default"]["threshold"]

  standby_pktime    = setup["asic_settings"]["standby"]["pktime"]
  standby_gain      = setup["asic_settings"]["standby"]["gain"]
  standby_threshold = setup["asic_settings"]["standby"]["threshold"]

  

  for board_name in board_list:
    board_info = db.find_board_by_name(board_name)
    conn = board_info["tdc_connector"]
    tdc_addr = board_info["tdc_addr"]

    standby = False
    if "standby" in board_info:
      if board_info["standby"]:
        standby=True

    if tdc_addr[0:2].lower() == "0x":
      if standby:
        init_board(tdc_addr,conn,standby_pktime,standby_gain,standby_threshold)
      else:
        init_board(tdc_addr,conn,pktime,gain,threshold)
  return

def init_board_by_name(board_name):
  return init_boards_by_name([board_name])
