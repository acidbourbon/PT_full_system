
import os
import db

def set_baseline( TDC, channel,val):

  chip = db.calc_chip_from_channel(channel)
  conn = db.calc_connector_from_channel(channel)
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
  
  
def init_active_boards():
  
  setup     = db.get_setup_json()
  pktime    = setup["default_asic_settings"]["pktime"]
  gain      = setup["default_asic_settings"]["gain"]
  threshold = setup["default_asic_settings"]["threshold"]

  for board_name in db.active_board_list():
    board_info = db.find_board_by_name(board_name)
    conn = board_info["tdc_connector"]
    tdc_addr = board_info["tdc_addr"]
    if tdc_addr[0:2].lower() == "0x":
      init_board(tdc_addr,conn,pktime,gain,threshold)
  return

def init_board_by_name(board_name):
  
  setup     = db.get_setup_json()
  pktime    = setup["default_asic_settings"]["pktime"]
  gain      = setup["default_asic_settings"]["gain"]
  threshold = setup["default_asic_settings"]["threshold"]

  board_info = db.find_board_by_name(board_name)
  conn = board_info["tdc_connector"]
  tdc_addr = board_info["tdc_addr"]
  if tdc_addr[0:2].lower() == "0x":
    init_board(tdc_addr,conn,pktime,gain,threshold)
