#!/usr/bin/env python


import db
import sys
import os
import json


from prettytable import PrettyTable
from dialog import Dialog
import db_dialogs as dbd








###########     main entry point     ########

d = Dialog(dialog="dialog")
  
d.set_background_title("Manage boards")


while True:

  code, tag = d.menu("main menu",
    choices = [("1","enable/disable boards"),
               ("2","view/edit board json"),
               ("3","view/edit setup json"),
               ("4","add board"),
               ("z","exit")] )
  
  if code == d.DIALOG_OK:

    ## enable/disable boards ##
    if tag == "1":
      dbd.dialog_enable_disable()

    ## edit board json tags ##
    if tag == "2":
      code2, choice2 = dbd.dialog_board_list()
      if code2 == d.DIALOG_OK: 
        board_json = db.get_board_json_by_name(choice2)
        code_21, text_21 = dbd.dialog_editbox(json.dumps(board_json,indent=2))  
        if code_21 == d.DIALOG_OK:
          db.write_board_json_by_name(choice2,json.loads(text_21))

    ## edit complete setup json ##
    if tag == "3":
      code_3, text = dbd.dialog_editbox(json.dumps(db.get_setup_json(),indent=2))
      if code_3 == d.DIALOG_OK:
        db.write_setup_json(json.loads(text))
      
  else:
    exit()







while 0:
  
  print "TDCs:" 
  tdc_t = PrettyTable(["TDC"])
  for tdc_addr in db.tdc_list():
    tdc_t.add_row([tdc_addr])
  print tdc_t
  print 
  print
  print "boards:"
  boards_t = PrettyTable(["TDC","CONN","board name","active","bl calib"])
  for board_name in db.board_list():
    board_info = db.find_board_by_name(board_name)
    board_calib = db.get_calib_json_by_name(board_name)
    got_bl_calib = "-"
    if "baselines" in board_calib:
      got_bl_calib = "yes"
    boards_t.add_row( [board_info["tdc_addr"], board_info["tdc_connector"], board_name, board_info["active"], got_bl_calib ] ) 

  print boards_t  

  print "main menu"
  a=sys.stdin.readline()

  if a == "q\n" or a== "quit\n" or a== "exit\n":
    exit()



