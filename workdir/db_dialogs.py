

import db
import sys
import tempfile
import os

from dialog import Dialog



def dialog_enable_disable():

  d = Dialog(dialog="dialog")
  
  d.set_background_title("Manage boards")
  
  choices = []
  info_format = "{:>8s}  {:>8s}"
  info = info_format.format("TDC", "CONN")
  choices += [("board",info, False)]


  board_list = db.board_list()
  
  for board_name in board_list:
    board_info = db.find_board_by_name(board_name)
    board_calib = db.get_calib_json_by_name(board_name)
    got_bl_calib = "-"
    if "baselines" in board_calib:
      got_bl_calib = "yes"
  
    active = board_info["active"]
  
    info = info_format.format(board_info["tdc_addr"], str(board_info["tdc_connector"]))
    choices += [(board_name,info, active)]
  
  
  code, active_boards = d.checklist("enable/disable boards",
                           choices= choices)

  if code == d.DIALOG_OK:
    for board_name in board_list:
      db.update_board_json_by_name(board_name,{"active":0})
    for board_name in active_boards:
      if not(board_name == "board"):
        db.update_board_json_by_name(board_name,{"active":1})
    

def dialog_board_list():

  d = Dialog(dialog="dialog")
  d.set_background_title("view boards")

  choices = []
  info_format = "{:>8s}  {:>8s}"
  info = info_format.format("TDC", "CONN")
  choices += [("board",info)]

  board_list = db.board_list()
  
  for board_name in board_list:
    board_info = db.find_board_by_name(board_name)
    board_calib = db.get_calib_json_by_name(board_name)
  
    info = info_format.format(board_info["tdc_addr"], str(board_info["tdc_connector"]))
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

