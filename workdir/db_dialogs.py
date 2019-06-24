

import db
import sys
import tempfile
import os
import pasttrec_ctrl as ptc
import misc

from dialog import Dialog


  
def gen_baseline_report(board_name,**kwargs):

  import pandas as pd
  import numpy as np
  calib_json = db.get_calib_json_by_name(board_name,**kwargs)
  if "baselines" in calib_json:
    baselines = calib_json["baselines"]
    baseline_mean = baselines
    if "baseline_mean" in calib_json:
      baseline_mean = calib_json["baseline_mean"]
    baseline_stddev = calib_json["baseline_stddev"]
    ch_error = calib_json["ch_error"]
    bl_range = calib_json["bl_range"]
    board_info = db.find_board_by_name(board_name)
    channels = board_info["channels"]
    noise_scan_raw = calib_json["noise_scan_raw"]
    noise_scan_x = calib_json["bl_range"]

    df = pd.DataFrame(
       np.transpose(np.array([baselines,baseline_mean,baseline_stddev,ch_error])),
      index= channels, columns=["baseline","bl_mean","bl_stddev","error"]
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
    return report
  else:
    return 0

def board_baseline_report(board_name,**kwargs):

  ### if you want to display the dummy baseline calib
  ### use board_baseline_report(board_name,dummy_calib=True)

  dummy_calib = kwargs.get("dummy_calib",False)

  d = Dialog(dialog="dialog")

  report_calib = gen_baseline_report(board_name)
  report_dummy = ""
  report = report_calib
  if dummy_calib and report_calib:
    report_dummy = gen_baseline_report(board_name,dummy_calib=True)
    report_calib = "\n  #####  calib  ##### \n\n\n" + report_calib
    report_dummy = "\n  #####  dummy  ##### \n\n\n" + report_dummy
    report = misc.side_by_side(report_calib,report_dummy,width=60)
  elif dummy_calib:
    report_dummy = gen_baseline_report(board_name,dummy_calib=True)
    report_dummy = "\n  #####  dummy  ##### \n\n\n" + report_dummy
    report = report_dummy

  if report: 
    code_21, text_21 = dialog_editbox(report)  
  else:
    d.msgbox("no baseline info, not calibrated")





def dialog_board_list(**kwargs):

  width = str(100)
  height = str(30)
  menu_height = str(28)
  list_height = menu_height
  
  checklist = kwargs.get("checklist","")

  check_enable  = False
  check_standby = False
  if checklist == "enable":
    check_enable = True
  if checklist == "standby":
    check_standby = True


  d = Dialog(dialog="dialog")
  d.set_background_title("view boards")
  if check_enable:
    d.set_background_title("enable/disable boards")
  if check_standby:
    d.set_background_title("set boards to standby")

  choices = []
  info_format = "{:>6s}  {:>4s}  {:>7s}  {:>5}  {:>12s}  {:>6s}  {:>6s}  {:>6s}  {:>7s}"
  info = info_format.format("TDC", "CONN","chamber","layer","FPC ABCD", "BL cal", "t1 cal", "active","standby")

  if check_enable or check_standby:
    choices += [("board",info, False)]
  else:
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
    active_bool = False
    if board_info["active"]:
      active = "yes"
      active_bool = True

    standby = " - "
    standby_bool = False
    if "standby" in board_info:
      if board_info["standby"]:
        standby = "yes"
        standby_bool = True
  
    info = info_format.format(
      board_info["tdc_addr"],
      str(board_info["tdc_connector"]),
      str(board_info["chamber"]),
      str(board_info["layer"]),
      str(board_info["fpc_a"]).rjust(2)+","+
      str(board_info["fpc_b"]).rjust(2)+","+
      str(board_info["fpc_c"]).rjust(2)+","+
      str(board_info["fpc_d"]).rjust(2),
      bl_calib, t1_calib, active, standby )
    if check_enable:
      choices += [(board_name,info, active_bool)]
    elif check_standby:
      choices += [(board_name,info, standby_bool)]
    else:
      choices += [(board_name,info)]
  
  

  if check_enable:
    code, active_boards = d.checklist("enable/disable boards", choices=choices, width=width, height=height, list_height=list_height)
    if code == d.DIALOG_OK:
      for board_name in board_list:
        db.disable_board(board_name)
      for board_name in active_boards:
        if not(board_name == "board"):
          db.enable_board(board_name)

  elif check_standby:
    code, standby_boards = d.checklist("set board standby", choices= choices, width=width,height=height,list_height=list_height)
    if code == d.DIALOG_OK:
      for board_name in board_list:
        db.unset_standby_board(board_name)
      for board_name in standby_boards:
        if not(board_name == "board"):
          db.set_standby_board(board_name)

  else:
    code, tag = d.menu("select a board:",
                     choices= choices ,width=width,height=height,menu_height=menu_height)
    return code, tag



def dialog_enable_disable():
  return dialog_board_list(checklist="enable")

def dialog_standby():
  return dialog_board_list(checklist="standby")

    
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

