#!/usr/bin/env python


import db
import sys
import os
import json


from prettytable import PrettyTable
from dialog import Dialog
import db_dialogs as dbd
import tdc_daq as td
import pasttrec_ctrl as ptc








###########     main entry point     ########

d = Dialog(dialog="dialog")
  
d.set_background_title("Manage boards")

db.write_go4_settings_h()

mm_tag = ""

while True:


  if mm_tag == "":
    code, tag = d.menu("main menu", height="30", menu_height="28",
      choices = [
                 ("m1","--- operation ---"),
                 ("m2","--- calibration ---"),
                 ("m3","--- config/view/edit ---"),
                 ("m4","--- housekeeping ---"),
                 ("m5","--- test procedures ---"),
                 ("z","exit")] )
    if code == d.DIALOG_OK:
      mm_tag = tag



  if mm_tag == "m1":
    code, tag = d.menu("operation", height="30", menu_height="28",
    choices = [
               ("1","view boards - enable/disable boards"),
               ("35","set boards to standby"),
               ("8","init ASICs (active boards)"),
               ("31","slow control test (active boards)"),
               ("13","get t1 and tot of board"),
               ("14","reset board"),
               ("27","set min threshold"),
               ("28","set max threshold"),
               ("29","set threshold")
              ])
  if mm_tag == "m2":
    code, tag = d.menu("calibration", height="30", menu_height="28",
    choices = [
             ##("9","auto calib baselines of board"), ## we don't use the tot method anymore
             ("1","view boards - enable/disable boards"),
             ("15","calib baselines (noise method) of board"),
             ("30"," ... for all active boards"),
             ("16","view board baseline calib"),
             ("33","dummy calib baselines of board"),
             ("34","view baseline dummy calib"),
             ("21","view/edit board calib json"),
             ("12","auto calib t1 offsets of board"),
             ("18","clear t1 offsets of board"),
             ("20","clear t1 offsets of tdc"),
             (""," "),
             (""," --- experimental methods ---"),
             ("32","calib baselines (noise method, per channel) of board")
              ])
  if mm_tag == "m3":
    code, tag = d.menu("edit/config", height="30", menu_height="28",
    choices = [
             ("1","view boards - enable/disable boards"),
             ("7","edit default asic settings"),
             ("17","edit global settings"),
             ("2","view/edit board json"),
             ("21","view/edit board calib json"),
             ("19","view/edit tdc json"),
             ("3","view/edit setup json")
              ])
  if mm_tag == "m4":
    code, tag = d.menu("housekeeping", height="30", menu_height="28",
    choices = [
             ("24","view board list"),
             ("25","view tdc list"),
             ("26","view hub list"),
             ("4","add board"),
             ("6","move board"),
             ("5","remove board"),
             ("10","add tdc"),
             ("11","remove tdc"),
             ("22","add hub"),
             ("23","remove hub")
              ])
  if mm_tag == "m5":
    code, tag = d.menu("test procedures", height="30", menu_height="28",
    choices = [
               ("1","view boards - enable/disable boards"),
               ("31","slow control test (active boards)"),
               ("13","get t1 and tot of board"),
               ("33","dummy calib baselines of board"),
               ("34","view baseline dummy calib")
              ])


  if code == d.DIALOG_OK:

    ## enable/disable boards ##
    if tag == "1":
      dbd.dialog_enable_disable()
      td.enable_tdc_channels_of_active_boards()

    ## set boards to standby ##
    if tag == "35":
      dbd.dialog_standby()
      td.enable_tdc_channels_of_active_boards()

    ## edit board json tags ##
    if tag == "2":
      while True:
        code2, choice2 = dbd.dialog_board_list()
        if code2 == d.DIALOG_OK: 
          board_json = db.get_board_json_by_name(choice2)
          code_21, text_21 = dbd.dialog_editbox(json.dumps(board_json,indent=2,sort_keys=True))  
          if code_21 == d.DIALOG_OK:
            db.write_board_json_by_name(choice2,json.loads(text_21))
        else:
          break

    ## edit complete setup json ##
    if tag == "3":
      code_3, text = dbd.dialog_editbox(json.dumps(db.get_setup_json(),indent=2,sort_keys=True))
      if code_3 == d.DIALOG_OK:
        db.write_setup_json(json.loads(text))
     
    ## add board ##
    if tag == "4":
      code_4, tdc_addr = dbd.dialog_tdc_list()
      if code_4 == d.DIALOG_OK:

        while True:
          code_41, conn_str = dbd.dialog_connector_list(tdc_addr)
          if code_41 == d.DIALOG_OK:
            conn = int(conn_str)
            if not db.find_board_by_tdc_connector(tdc_addr,int(conn_str)):
              code_42, name_str = d.inputbox(text="enter board name",init="0000")
              if code_42 == d.DIALOG_OK:
                code_43, calib_file = d.inputbox(text="enter calib file name",init="./boards/board_"+name_str+".json")
                if code_43 == d.DIALOG_OK:
                  code_44, str_44 = d.inputbox(text="enter drift chamber number",init="0")
                  if code_44 == d.DIALOG_OK:
                    code_45, str_45 = d.inputbox(text="enter sense wire layer",init="0")
                    if code_45 == d.DIALOG_OK:
                      code_455, tag_455 = d.menu("wire to channel mapping",\
                        choices = [("1","reverse wire->channel mapping"), ("0","ascending wire->channel mapping")   ])
                      if code_455 == d.DIALOG_OK:
                        code_46, str_46 = d.inputbox(text="enter chamber FPC number (start w/ 0) for FPC conn A (PT chan 1-4)",init="")
                        if code_46 == d.DIALOG_OK:
                          code_47, str_47 = d.inputbox(text="enter chamber FPC number (start w/ 0) for FPC conn B (PT chan 5-8)",init="")
                          if code_47 == d.DIALOG_OK:
                            code_48, str_48 = d.inputbox(text="enter chamber FPC number (start w/ 0) for FPC conn C (PT chan 9-12)",init="")
                            if code_48 == d.DIALOG_OK:
                              code_49, str_49 = d.inputbox(text="enter chamber FPC number (start w/ 0) for FPC conn D (PT chan 13-16)",init="")
                              if code_49 == d.DIALOG_OK:
                                chamber_no = int(str_44)
                                layer_no   = int(str_45)
                                fpc_a_no     = int(str_46)
                                fpc_b_no     = int(str_47)
                                fpc_c_no     = int(str_48)
                                fpc_d_no     = int(str_49)
                                reverse_mapping = int(tag_455) 

                                print "adding"
                                print tdc_addr
                                print conn_str
                                print name_str
                                print calib_file
                                db.add_board_json(tdc_addr,{ "name":name_str, "tdc_connector":conn,\
                                    "chamber":chamber_no,\
                                    "layer":layer_no,\
                                    "fpc_a":fpc_a_no,\
                                    "fpc_b":fpc_b_no,\
                                    "fpc_c":fpc_c_no,\
                                    "fpc_d":fpc_d_no,\
                                    "reverse_mapping":reverse_mapping,\
                                    "calib_file":calib_file, "active":0 })
              break
            else:
              d.msgbox("this connector is already occupied :(")

    ## remove board ##
    if tag == "5":
      while True:
        code_5, choice_5 = dbd.dialog_board_list()
        if code_5 == d.DIALOG_OK: 
          db.remove_board(choice_5)
        else:
          break

    ## move board ##
    if tag == "6":
      while True:
        code_6, board_name = dbd.dialog_board_list()
        if code_6 == d.DIALOG_OK: 
          code_61, tdc_addr = dbd.dialog_tdc_list()
          if code_61 == d.DIALOG_OK:
            while True:
              code_62, conn_str = dbd.dialog_connector_list(tdc_addr)
              if code_62 == d.DIALOG_OK:
                if not db.find_board_by_tdc_connector(tdc_addr,int(conn_str)):
                  if code_62 == d.DIALOG_OK:
                    board_json = db.get_board_json_by_name(board_name)
                    db.remove_board(board_name)
                    board_json["tdc_connector"] = int(conn_str)
                    db.add_board_json(tdc_addr,board_json)
                    d.msgbox("board was moved in database")
                  break
                else:
                  d.msgbox("this connector is already occupied :(")
              else:
                break
            
        else:
          break

    ## edit default asic settings ##
    if tag == "7":
      code_7, text = dbd.dialog_editbox(json.dumps(db.get_setup_json()["default_asic_settings"],indent=2,sort_keys=True))
      if code_7 == d.DIALOG_OK:
        setup = db.get_setup_json()
        default_asic_settings = json.loads(text)
        setup["default_asic_settings"] = default_asic_settings;
        db.write_setup_json(setup)

        code = d.yesno("do you wish to reprogram ASICs with the new settings?")
        if code == d.DIALOG_OK:
          ptc.init_active_boards()
          d.msgbox("initialized all active boards\nand enabled respective TDC channels")

    ## threshold all min
    if tag == "27":
      setup = db.get_setup_json()
      current_thresh = setup["default_asic_settings"]["threshold"]
      setup["default_asic_settings"]["threshold"] = 0
      db.write_setup_json(setup)
      ptc.init_active_boards()
      setup["default_asic_settings"]["threshold"] = current_thresh
      db.write_setup_json(setup)

    ## threshold all max
    if tag == "28":
      setup = db.get_setup_json()
      current_thresh = setup["default_asic_settings"]["threshold"]
      setup["default_asic_settings"]["threshold"] = 127
      db.write_setup_json(setup)
      ptc.init_active_boards()
      setup["default_asic_settings"]["threshold"] = current_thresh
      db.write_setup_json(setup)

    ## set threshold
    if tag == "29":
      setup = db.get_setup_json()
      current_thresh = setup["default_asic_settings"]["threshold"]
      code, thresh_str = d.inputbox(text="enter temporary threshold (default={:d})".format(current_thresh),init=str(current_thresh))
      if code == d.DIALOG_OK:
        setup["default_asic_settings"]["threshold"] = int(thresh_str)
        db.write_setup_json(setup)
        ptc.init_active_boards()
        setup["default_asic_settings"]["threshold"] = current_thresh
        db.write_setup_json(setup)
   
    if tag == "8":
      td.enable_tdc_channels_of_active_boards()
      ptc.init_active_boards()
      d.msgbox("initialized all active boards\nand enabled respective TDC channels")
      
    ## calib board baselines ##
    if tag == "9":
      code_9, choice_9 = dbd.dialog_board_list()
      if code_9 == d.DIALOG_OK:
        board_name = choice_9
        d.msgbox("Supply standard test pulse to all inputs of board {:s} simultaneously:\n-2V, negative polarity, duration 10 ns, supplied to input\
via AC coupling and 10k resistor.".format(board_name) )
        import baseline_calib
        baseline_calib.baseline_calib(board_name)


    ## remove tdc ##
    if tag == "11":
      while True:
        code, choice = dbd.dialog_tdc_list()
        if code == d.DIALOG_OK: 
          db.remove_tdc(choice)
        else:
          break

    ## add tdc ##
    if tag == "10":
      code, hub_addr = dbd.dialog_hub_list()
      if code == d.DIALOG_OK:
        code, tdc_addr = d.inputbox(text="enter tdc addr",init="")
        if code == d.DIALOG_OK:
          code, tdc_name = d.inputbox(text="enter tdc name",init=tdc_addr)
          if code == d.DIALOG_OK:
            code, channels_str = d.inputbox(text="enter number of channels",init="48")
            if code == d.DIALOG_OK:
              code, connectors_str = d.inputbox(text="enter number of connectors",init="{:d}".format(int(channels_str)/16))
              if code == d.DIALOG_OK:
                db.insert_tdc(hub_addr,tdc_addr,tdc_name,int(channels_str),int(connectors_str))

    ## add hub ##
    if tag == "22":
      code, hub_addr = d.inputbox(text="enter hub addr",init="")
      if code == d.DIALOG_OK:
        code, hub_name = d.inputbox(text="enter hub name",init=hub_addr)
        if code == d.DIALOG_OK:
          db.insert_hub(hub_addr,hub_name)

    ## remove hub ##
    if tag == "23":
      while True:
        code, choice = dbd.dialog_hub_list()
        if code == d.DIALOG_OK: 
          db.remove_hub(choice)
        else:
          break

    ## view board list ##
    if tag == "24":
      code, choice = dbd.dialog_board_list()

    ## view tdc list ##
    if tag == "25":
      code, choice = dbd.dialog_tdc_list()

    ## view hub list ##
    if tag == "26":
      code, choice = dbd.dialog_hub_list()
      

    ## calib t1 offsets ##
    if tag == "12":
      code_9, choice_9 = dbd.dialog_board_list()
      if code_9 == d.DIALOG_OK:
        board_name = choice_9
        board_info = db.find_board_by_name(board_name)
        if board_info["baseline_is_calibrated"]:
          d.msgbox("Supply the same pulse to all inputs of board {:s} simultaneously to calibrate t1 offsets".format(board_name) )
          td.calib_t1_offsets_of_board(board_name)
        else:
          d.msgbox("t1 calibration not possible. Please calibrate baselines first, or the walk effect might skew your t1 calibration.")

    ## clear t1 offsets ##
    if tag == "18":
      code_9, choice_9 = dbd.dialog_board_list()
      if code_9 == d.DIALOG_OK:
        board_name = choice_9
        db.clear_t1_offsets_of_board(board_name)
        d.msgbox("cleared" )


    ## read t1 tot of board ##
    if tag == "13":
      code, board_name = dbd.dialog_board_list()
      if code == d.DIALOG_OK:
        code, no_pulses_str = d.inputbox(text="enter number of pulses to record",init="100")
        if code == d.DIALOG_OK:
          no_pulses = int(no_pulses_str)
          td.record_tree_data(no_pulses)

          import pandas as pd
          import numpy as np

          t1, t1_stdev, tot, tot_stdev, counts = td.get_t1_tot_of_board(board_name)

          board_info = db.find_board_by_name(board_name)
          channels = board_info["channels"]

          df = pd.DataFrame(np.transpose(np.array([t1,t1_stdev,tot,tot_stdev,counts])), index= channels, columns=["t1","t1_stdev","tot","tot_stdev","counts"] )

          ##answer = { "channels": board_info["channels"], "t1":t1, "tot":tot, "counts":counts}
          ##code_21, text_21 = dbd.dialog_editbox(json.dumps(answer,indent=2,sort_keys=True))  
          #t = PrettyTable(["channel","t1","tot","counts"])
          #for i in range(0,len(channels)):
          #  t.add_row(["{:d}".format(channels[i]), "{:3.3f}".format(t1[i]), "{:3.3f}".format(tot[i]), "{:.0f}".format(counts[i])  ])
      
          #code_21, text_21 = dbd.dialog_editbox(t.get_string())  
          report = df.to_string()
          report += "\n\n\n"
          report += df.describe().to_string()
          code_21, text_21 = dbd.dialog_editbox(report)  

    ## slow control test of active boards ##
    if tag == "31":
      #test_results = ptc.slow_control_test_active_boards()
      #code_21, text_21 = dbd.dialog_editbox(json.dumps(test_results, indent=2, sort_keys=True))
      dbd.dialog_slow_control_test()

                 
      
    ## reset board ##
    if tag == "14":
      code, board_name = dbd.dialog_board_list()
      if code == d.DIALOG_OK:
        ptc.reset_board_by_name(board_name)
      
    ## calib board baselines ##
    if tag == "15":
      code_15, choice_15 = dbd.dialog_board_list()
      if code_15 == d.DIALOG_OK:
        board_name = choice_15
        d.msgbox("Disconnect board {:s} from detector or cut voltage of detector to measure pure electronic noise".format(board_name) )
        import baseline_calib
        baseline_calib.baseline_calib_by_noise(board_name)
        
        dbd.board_baseline_report(board_name)

    ## dummy calib / scan board baselines ##
    if tag == "33":
      code_15, choice_15 = dbd.dialog_board_list()
      if code_15 == d.DIALOG_OK:
        board_name = choice_15
        import baseline_calib
        baseline_calib.baseline_calib_by_noise(board_name,dummy_calib=True)
        
        dbd.board_baseline_report(board_name,dummy_calib=True)

    ## view dummy calib ##
    if tag == "34":
      code_15, choice_15 = dbd.dialog_board_list()
      if code_15 == d.DIALOG_OK:
        board_name = choice_15
        
        dbd.board_baseline_report(board_name,dummy_calib=True)

    ## calib board baselines, individual channels ##
    if tag == "32":
      code_15, choice_15 = dbd.dialog_board_list()
      if code_15 == d.DIALOG_OK:
        board_name = choice_15
        d.msgbox("Disconnect board {:s} from detector or cut voltage of detector to measure pure electronic noise".format(board_name) )
        import baseline_calib
        baseline_calib.baseline_calib_by_noise(board_name,individual=True)
        
        baselines = db.get_calib_json_by_name(board_name)["baselines"]
        board_info = db.find_board_by_name(board_name)
        channels = board_info["channels"]
        dbd.board_baseline_report(board_name)
    
    ## calib board baselines of all active boards
    if tag == "30":
      import baseline_calib
      for board_name in db.active_board_list():
        print "calibrating board {:s}".format(board_name)
        baseline_calib.baseline_calib_by_noise(board_name)
        print "done"


    ## view board baselines ##
    if tag == "16":
      while True:
        code_15, choice_15 = dbd.dialog_board_list()
        if code_15 == d.DIALOG_OK:
          board_name = choice_15
          dbd.board_baseline_report(board_name)
            
        else:
          break

    ## edit global settings ##
    if tag == "17":
      code_17, text = dbd.dialog_editbox(json.dumps(db.get_setup_json()["global_settings"],indent=2,sort_keys=True))
      if code_17 == d.DIALOG_OK:
        setup = db.get_setup_json()
        global_settings = json.loads(text)
        setup["global_settings"] = global_settings;
        db.write_setup_json(setup)

    ## edit tdc json ##
    if tag == "19":
      code, tdc_addr = dbd.dialog_tdc_list()
      if code == d.DIALOG_OK: 
        tdc_json = db.get_tdc_json(str(tdc_addr))
        code_17, text = dbd.dialog_editbox(json.dumps(tdc_json,indent=2,sort_keys=True))
        if code_17 == d.DIALOG_OK:
          tdc_json = json.loads(text)
          db.write_tdc_json(str(tdc_addr),tdc_json)

    ## clear t1 offsets of tdc ##
    if tag == "20":
      code, tdc_addr = dbd.dialog_tdc_list()
      if code == d.DIALOG_OK: 
        db.clear_t1_offsets_of_tdc(tdc_addr)
        d.msgbox("cleared" )

    ## edit board calib ##
    if tag == "21":
      code, board = dbd.dialog_board_list()
      if code == d.DIALOG_OK: 
        calib_json = db.get_calib_json_by_name(board)
        code_17, text = dbd.dialog_editbox(json.dumps(calib_json,indent=2,sort_keys=True))
        if code_17 == d.DIALOG_OK:
          calib_json = json.loads(text)
          db.write_calib_json_by_name(board,calib_json)

      
    if tag == "z":
      exit()
    
      
  else:
    mm_tag = ""







