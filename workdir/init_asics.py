#!/usr/bin/env python




import tdc_daq as td
import db
import pasttrec_ctrl as ptc



### disable all daq channels of listed TDCs

for tdc_addr in db.tdc_list():
  td.disable_channels(tdc_addr,range(0,32))

for board_name in db.active_board_list():
  board_info = db.find_board_by_name(board_name)
  channels = board_info["channels"]
  tdc_addr = board_info["tdc_addr"]
  td.enable_channels(tdc_addr,channels)
