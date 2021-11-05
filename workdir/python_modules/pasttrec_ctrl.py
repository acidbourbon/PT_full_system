
import os
import db
import tdc_daq
from time import sleep

from trbnet import TrbNet

lib = '/trbnettools/trbnetd/libtrbnet.so'
host = os.getenv("DAQOPSERVER")

t = TrbNet(libtrbnet=lib, daqopserver=host)


global_settings = db.get_global_settings()
slow_control_log = 0
if ("slow_control_log" in global_settings):
  if (global_settings["slow_control_log"] == 1):
    slow_control_log = 1

slow_control_log_file = "./slow_control.log"




black_settings_pt15_g1_thr127 = [
  0x019,
  0x11e,
  0x215,
  0x37f,
  0x40f,
  0x50f,
  0x60f,
  0x70f,
  0x80f,
  0x90f,
  0xa0f,
  0xb0f
]

black_settings_pt20_g1_thr127 = [
  0x01a,
  0x11e,
  0x215,
  0x37f,
  0x40f,
  0x50f,
  0x60f,
  0x70f,
  0x80f,
  0x90f,
  0xa0f,
  0xb0f
]

blue_settings_pt10_g1_thr127 = [
  0x018,
  0x11e,
  0x215,
  0x37f,
  0x40f,
  0x50f,
  0x60f,
  0x70f,
  0x80f,
  0x90f,
  0xa0f,
  0xb0f
]

spi_queue = 0
spi_mem = {}

def spi(TDC_str,CONN,CHIP, data_list, **kwargs):
  f = ""
  if (slow_control_log):
    f = open(slow_control_log_file,"a")

  
  TDC = int(TDC_str,16)
  
  
  if ( not( TDC in spi_mem ) ):
    spi_mem[TDC] = {}
  if ( not( CONN in spi_mem[TDC] ) ):
    spi_mem[TDC][CONN] = {}
  if ( not( CHIP in spi_mem[TDC][CONN] ) ):
    spi_mem[TDC][CONN][CHIP] = []
  
  if spi_queue:
    
    spi_mem[TDC][CONN][CHIP] += data_list
  
  else:
 
    my_data_list = spi_mem[TDC][CONN][CHIP] + data_list
    spi_mem[TDC][CONN][CHIP].clear() # empty queue
 
    header = 0x52000
    if( CHIP == 1 ):
      header = 0x54000
      
    # bring all CS (reset lines) in the default state (1) - upper four nibbles: invert CS, lower four nibbles: disable CS
    t.trb_register_write(TDC, 0xd417, 0x0000FFFF)
    if (slow_control_log):
      f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd417, 0x0000FFFF))


    # (chip-)select output $CONN for i/o multiplexer reasons, remember CS lines are disabled
    t.trb_register_write(TDC, 0xd410, 0xFFFF & ( 1<<(CONN-1) ) )
    if (slow_control_log):
      f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd410, 0xFFFF & ( 1<<(CONN-1) ) ))

    # override: (chip-) select all ports!!
    #trbcmd w $TDC 0xd410 0xFFFF

    # override: (chip-) select nothing !!
    #trbcmd w $TDC 0xd410 0x0000

    # disable all SDO outputs but output $CONN
    t.trb_register_write(TDC, 0xd415, 0xFFFF & ~(1<<(CONN-1)) )
    if (slow_control_log):
      f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd415, 0xFFFF & ~(1<<(CONN-1)) ))

    # disable all SCK outputs but output $CONN
    t.trb_register_write(TDC, 0xd416, 0xFFFF & ~(1<<(CONN-1)) )
    if (slow_control_log):
      f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd416, 0xFFFF & ~(1<<(CONN-1)) ))

    # override: disable all SDO and SCK lines
    #trbcmd w $TDC 0xd415 0xFFFF
    #trbcmd w $TDC 0xd416 0xFFFF

    for data in my_data_list:
      # writing one data word, append zero to the data word, the chip will get some more SCK clock cycles
      t.trb_register_write(TDC, 0xd400, (header+data)<<4 )
      if (slow_control_log):
        f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd400, (header+data)<<4 ))
      
      # write 1 to length register to trigger sending
      t.trb_register_write(TDC, 0xd411, 0x0001)
      if (slow_control_log):
        f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd411, 0x0001))

  if (slow_control_log):
    f.close()
    

def reset_board(TDC_str,CONN):
  f = ""
  if (slow_control_log):
    f = open(slow_control_log_file,"a")
  
  TDC = int(TDC_str,16)

  # bring all CS (reset lines) in the default state (1) - upper four nibbles: invert CS, lower four nibbles: disable CS
  # ergo enable CS, because we need it for the reset
  #trbcmd w $TDC 0xd417 0x00000000

  # make selection mask from $CONN 
  sel_mask= 0xFFFF & (1<<(CONN-1))

  # bring all CS (reset lines) in the default state (1) - upper four nibbles: invert CS, lower four nibbles: disable CS
  t.trb_register_write(TDC, 0xd417, 0x0000FFFF)
  if (slow_control_log):
    f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd417, 0x0000FFFF))

  # (chip-)select output $CONN for i/o multiplexer reasons, remember CS lines are disabled
  #trbcmd w $TDC 0xd410 0x0000$sel_mask

  # bring CS low for sel mask, i.e. invert CS for sel mask, keep CS disabled
  t.trb_register_write(TDC, 0xd417, (sel_mask<<16) + 0xFFFF)
  if (slow_control_log):
    f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd417, (sel_mask<<16) + 0xFFFF))

  for i in range(1, 26):
    # generate 25 clock cycles
    # invert SCK for selection mask

    # upper four nibbles: invert SCK, lower four nibbles disable SCK
    t.trb_register_write(TDC, 0xd416, sel_mask<<16)
    if (slow_control_log):
      f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd416, sel_mask<<16))

    # restore SCK to default state
    t.trb_register_write(TDC, 0xd416, 0x00000000)
    if (slow_control_log):
      f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd416, 0x00000000))

  # bring CS to standard position (HI) again, keep CS disabled
  t.trb_register_write(TDC, 0xd417, 0x0000FFFF)
  if (slow_control_log):
    f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xd417, 0x0000FFFF))

  if (slow_control_log):
    f.close()
 


def set_threshold(TDC,CONN,CHIP,THR):
  spi(TDC,CONN,CHIP, [ 0x300 + (0xFF & THR)])



def slow_control_test(board_name):
  
  scan_time = 0.2
  
  board_info = db.find_board_by_name(board_name)
  channels   = board_info["channels"] # zero based 
  TDC        = board_info["tdc_addr"]
  connector  = board_info["tdc_connector"]

  db.enable_board(board_name)
  init_board_by_name(board_name)

  
  print( "slow control test of board "+board_name )
  set_threshold_for_board(TDC,connector,0)
  rates_lo_thr = tdc_daq.scaler_rate(TDC,channels,scan_time)

  set_threshold_for_board(TDC,connector,127)
  rates_hi_thr = tdc_daq.scaler_rate(TDC,channels,scan_time)
  state_hi_thr = tdc_daq.read_ch_state(TDC,channels)
 
  print( "rates low thr" )
  print( rates_lo_thr )
  print( "rates high thr" )
  print( rates_hi_thr )
  print( "state high thr" )
  print( state_hi_thr )


  ## restore threshold again - a bit dirty but faster than complete init again
  setup     = db.get_setup_json()

  #pktime    = setup["asic_settings"]["default"]["pktime"]
  #gain      = setup["asic_settings"]["default"]["gain"]
  threshold = setup["asic_settings"]["default"]["threshold"]

  #standby_pktime    = setup["asic_settings"]["standby"]["pktime"]
  #standby_gain      = setup["asic_settings"]["standby"]["gain"]
  standby_threshold = setup["asic_settings"]["standby"]["threshold"]

  standby = False
  if "standby" in board_info:
    if board_info["standby"]:
      standby=True

  if standby:
    set_threshold_for_board(TDC,connector,standby_threshold)
  else:
    set_threshold_for_board(TDC,connector,threshold)
  ## end of restore threshold

  if state_hi_thr == [1]*len(channels) and rates_hi_thr == [0]*len(channels) and rates_lo_thr != [0]*len(channels):
    return 1
  else:
    return 0

def set_baseline( TDC, channel,value):

  chip = db.calc_chip_from_channel(channel)
  conn = db.calc_connector_from_channel(channel)
  chip_chan=channel%8

  val  = value + 15 
  chan = chip_chan + 4 

  spi(TDC,conn, chip, [ ((0xF & chan)<<8) + val] )

  return


def set_threshold_for_board(TDC,conn,thresh):
  set_threshold(TDC,conn,0,thresh)
  set_threshold(TDC,conn,1,thresh)
  

def set_threshold_for_board_by_name(board_name,thresh):
  
  setup     = db.get_setup_json()

  board_info = db.find_board_by_name(board_name)
  conn = board_info["tdc_connector"]
  tdc_addr = board_info["tdc_addr"]
  set_threshold_for_board(tdc_addr,conn,thresh)

  return


def set_all_baselines( TDC, channels, values): # channels and values have to have same dimensions
  #print("set baselines of the following channels")
  #print( channels )
  #print("to the following values")
  #print( values )
  index=0
  for i in channels:
    set_baseline(TDC,i,int(values[index]))
    index+=1
    
  return


def init_chip(TDC,CONN,CHIP,pktime,GAIN,thresh):
  # begin queueing
  spi_queue = 1
  
  if( pktime == 10 ):
    spi(TDC,CONN,CHIP,blue_settings_pt10_g1_thr127)
    if(GAIN == 4):
      spi(TDC,CONN,CHIP, [0x010])
    if(GAIN == 2):
      spi(TDC,CONN,CHIP, [0x014])
    if(GAIN == 1):
      spi(TDC,CONN,CHIP, [0x018])
    if(GAIN == 0):
      spi(TDC,CONN,CHIP, [0x01C])
      
  if( pktime == 15 ):
    spi(TDC,CONN,CHIP,black_settings_pt15_g1_thr127)
    if(GAIN == 4):
      spi(TDC,CONN,CHIP, [0x011])
    if(GAIN == 2):
      spi(TDC,CONN,CHIP, [0x015])
    if(GAIN == 1):
      spi(TDC,CONN,CHIP, [0x019])
    if(GAIN == 0):
      spi(TDC,CONN,CHIP, [0x01D])
    
  if( pktime == 20 ):
    spi(TDC,CONN,CHIP,black_settings_pt20_g1_thr127)
    if(GAIN == 4):
      spi(TDC,CONN,CHIP, [0x012])
    if(GAIN == 2):
      spi(TDC,CONN,CHIP, [0x016])
    if(GAIN == 1):
      spi(TDC,CONN,CHIP, [0x01a])
    if(GAIN == 0):
      spi(TDC,CONN,CHIP, [0x01E])
    
  #set_threshold(TDC,CONN,CHIP,thresh)
  
  board_info = db.find_board_by_tdc_connector(TDC,CONN)
  board_name = board_info["name"] 
  board_channels = board_info["channels"] 
  calib = db.get_calib_json_by_name(board_name)
  
  if ("baselines" in calib):
    board_baselines = calib["baselines"]
    channels = board_channels[0:9]
    values   = board_baselines[0:9]
    if CHIP == 1:
      channels = board_channels[8:17]
      values   = board_baselines[8:17]
    set_all_baselines(TDC,channels,values)
  set_threshold(TDC,CONN,CHIP,thresh)
  return

  # send all at once
  spi_queue = 0
  spi(TDC,CONN,CHIP,[])
  

def reset_board_by_name(board_name):
  board_info = db.find_board_by_name(board_name)
  conn = board_info["tdc_connector"]
  tdc_addr = board_info["tdc_addr"]
  if tdc_addr[0:2].lower() == "0x":
    reset_board(tdc_addr,conn)


def init_board(TDC,conn,pktime,gain,thresh):
  reset_board(TDC,conn)
  init_chip(TDC,conn,0,pktime,gain,thresh)
  init_chip(TDC,conn,1,pktime,gain,thresh)
  return
 

def slow_control_test_boards(board_list): 
  test_results = {}
  for board_name in board_list:
    answer = slow_control_test(board_name)
    test_results[board_name] = answer

  print( test_results )
  return test_results

def init_active_boards(pktime=-1,gain=-1,threshold=-1):
  return init_boards_by_name(db.active_board_list(),pktime,gain,threshold)

def init_boards_by_name(board_list,pktime=-1,gain=-1,threshold=-1):
  
  setup     = db.get_setup_json()
   
  if(pktime == -1): 
    pktime    = setup["asic_settings"]["default"]["pktime"]
  if(gain == -1):
    gain      = setup["asic_settings"]["default"]["gain"]
  if(threshold == -1):
    threshold = setup["asic_settings"]["default"]["threshold"]

  standby_pktime    = setup["asic_settings"]["standby"]["pktime"]
  standby_gain      = setup["asic_settings"]["standby"]["gain"]
  standby_threshold = setup["asic_settings"]["standby"]["threshold"]

  

  for board_name in board_list:
    #print("init board "+board_name)
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

def init_board_by_name(board,pktime=-1,gain=-1,threshold=-1):
  return init_boards_by_name([ board ],pktime,gain,threshold)
