

import db
import sys
import tempfile
import os
import pasttrec_ctrl as ptc
import misc

from dialog import Dialog


  



def board_baseline_report(board_name):
  import pandas as pd
  import numpy as np
  d = Dialog(dialog="dialog")
  calib_json = db.get_calib_json_by_name(board_name)
  if "baselines" in calib_json:
    baselines = calib_json["baselines"]
    baseline_stddev = calib_json["baseline_stddev"]
    ch_error = calib_json["ch_error"]
    bl_range = calib_json["bl_range"]
    board_info = db.find_board_by_name(board_name)
    channels = board_info["channels"]
    noise_scan_raw = calib_json["noise_scan_raw"]
    noise_scan_x = calib_json["bl_range"]

    df = pd.DataFrame(
       np.transpose(np.array([baselines,baseline_stddev,ch_error])),
      index= channels, columns=["baseline","stddev","error"]
    )
    report = df.to_string()
    report += "\n\n\n"
    report += df.describe().to_string()
    report += "\n\n\n"
    report += "\n\n\n"
    board_chan = 0
    for scan in noise_scan_raw:
      report += misc.ascii_hist(scan,xdata=noise_scan_x,title="PT "+board_name+" ch "+str(board_chan).rjust(2))
      report += "\n"*10
      board_chan += 1
    code_21, text_21 = dialog_editbox(report)  
  else:
    d.msgbox("no baseline info, not calibrated")

def dialog_enable_disable():

  d = Dialog(dialog="dialog")
  
  d.set_background_title("Manage boards")
  
  choices = []
  info_format = "{:>8s}  {:>8s}"
  info = info_format.format("TDC", "CONN")
  info_format = "{:>6s}  {:>4s}  {:>6s}  {:>6s}"
  info = info_format.format("TDC", "CONN", "BL cal", "t1 cal")
  choices += [("board",info, False)]


  board_list = db.board_list()
  
#  for board_name in board_list:
#    board_info = db.find_board_by_name(board_name)
#    board_calib = db.get_calib_json_by_name(board_name)
#    got_bl_calib = "-"
#    if "baselines" in board_calib:
#      got_bl_calib = "yes"
#  
#    active = board_info["active"]
#  
#    info = info_format.format(board_info["tdc_addr"], str(board_info["tdc_connector"]))
#    choices += [(board_name,info, active)]

  for board_name in board_list:
    board_info = db.find_board_by_name(board_name)
    board_calib = db.get_calib_json_by_name(board_name)
    
    bl_calib = " - "
    if board_info["baseline_is_calibrated"] == 1:
      bl_calib = "yes"
    elif board_info["baseline_is_calibrated"] == -1:
      bl_calib = "err"


    t1_calib = " - "
    if board_info["t1_is_calibrated"]:
      t1_calib = "yes"

    active =  board_info["active"]
  
    info = info_format.format(board_info["tdc_addr"], str(board_info["tdc_connector"]),  bl_calib, t1_calib,      )
#    choices += [(board_name,info)]
    choices += [(board_name,info, active)]
  
  
  
  code, active_boards = d.checklist("enable/disable boards",
                           choices= choices)

  if code == d.DIALOG_OK:
    for board_name in board_list:
      #db.update_board_json_by_name(board_name,{"active":0})
      db.disable_board(board_name)
    for board_name in active_boards:
      if not(board_name == "board"):
        #db.update_board_json_by_name(board_name,{"active":1})
        db.enable_board(board_name)
    
def dialog_tdc_list():

  d = Dialog(dialog="dialog")
  d.set_background_title("view TDCs")
  
  choices = []

  for tdc_addr in db.tdc_list():
    choices += [(tdc_addr, "")]

  return d.menu("select a tdc:", choices= choices )

def dialog_hub_list():

  d = Dialog(dialog="dialog")
  d.set_background_title("view hubs")
  
  choices = []

  for hub_addr in db.hub_list():
    choices += [(hub_addr, "")]

  return d.menu("select a hub:", choices= choices )

def dialog_connector_list(tdc_addr):

  d = Dialog(dialog="dialog")
  d.set_background_title("select connector")
  
  tdc_json = db.get_tdc_json_by_addr(tdc_addr)
  
  choices = []
  for i in range(1,tdc_json["connectors"]+1):
    choices += [(str(i),"TDC "+tdc_addr+" CONN "+str(i) )]

  return d.menu("select connector:", choices= choices )

  

def dialog_board_list():

  d = Dialog(dialog="dialog")
  d.set_background_title("view boards")

  choices = []
  info_format = "{:>6s}  {:>4s}  {:>6s}  {:>6s}  {:>6s}"
  info = info_format.format("TDC", "CONN", "BL cal", "t1 cal", "active")
  choices += [("board",info)]

  board_list = db.board_list()
  
  for board_name in board_list:
    board_info = db.find_board_by_name(board_name)
    board_calib = db.get_calib_json_by_name(board_name)
    
    bl_calib = " - "
    if board_info["baseline_is_calibrated"] == 1:
      bl_calib = "yes"
    elif board_info["baseline_is_calibrated"] == -1:
      bl_calib = "err"


    t1_calib = " - "
    if board_info["t1_is_calibrated"]:
      t1_calib = "yes"

    active = " - "
    if board_info["active"]:
      active = "yes"
  
    info = info_format.format(board_info["tdc_addr"], str(board_info["tdc_connector"]),  bl_calib, t1_calib, active       )
    choices += [(board_name,info)]
  
  

  code, tag = d.menu("select a board:",
                     choices= choices )
  #if code == d.DIALOG_OK:
  #  return tag
  #return 0
  return code, tag

def dialog_editbox(in_text):

  dummy, temp_path = tempfile.mkstemp()
  print temp_path

  f = open(temp_path, 'w')
  f.write( in_text)
  f.write("\n")
  f.close()

  d = Dialog(dialog="dialog")
  d.set_background_title("Manage boards")

  code, text = d.editbox(temp_path)
  os.remove(temp_path)
  return (code, text)


def dialog_slow_control_test():

  d = Dialog(dialog="dialog")
  d.set_background_title("view boards")

  choices = []
  info_format = "{:>6s}  {:>4s}  {:>6s}  {:>6s}  {:>6s}  {:>6s}"
  info = info_format.format("TDC", "CONN", "BL cal", "t1 cal", "active", "SloCon")
  choices += [("board",info)]

  board_list = db.active_board_list()

  test_results = ptc.slow_control_test_active_boards()
  
  for board_name in board_list:
    board_info = db.find_board_by_name(board_name)
    board_calib = db.get_calib_json_by_name(board_name)
    
    bl_calib = " - "
    if board_info["baseline_is_calibrated"] == 1:
      bl_calib = "yes"
    elif board_info["baseline_is_calibrated"] == -1:
      bl_calib = "err"


    t1_calib = " - "
    if board_info["t1_is_calibrated"]:
      t1_calib = "yes"

    active = " - "
    if board_info["active"]:
      active = "yes"

    sctest = "err"
    if test_results[board_name] == 1:
      sctest = " ok"
  
    info = info_format.format(board_info["tdc_addr"], str(board_info["tdc_connector"]),  bl_calib, t1_calib, active, sctest       )
    choices += [(board_name,info)]
  
  

  code, tag = d.menu("slow control test - active boards",
                     choices= choices, height="30", menu_height="28", width="70")

