#!/usr/bin/env python

import db
import os
import shutil

tdc_list = db.tdc_list();

shutil.rmtree("unify_channel_info")

os.mkdir("unify_channel_info")  

for tdc in tdc_list:

  ###offsets = db.get_t1_offsets(tdc)
  tdc_json = db.get_tdc_json(str(tdc))
  offsets = tdc_json["t1_offset"]
  connectors = tdc_json["connectors"]
  channels   = tdc_json["channels"]
  wire    = []
  layer   = []
  fpc     = []
  chamber = []
  for connector in range(1,connectors+1):
    board_info = db.find_board_by_tdc_connector(tdc,connector)
    if( board_info != 0 ):
      if "wires" in board_info:
        wire = wire + board_info["wires"]
      else:
        wire    = wire    + 16*[-1]

      if "layer" in board_info:
        layer = layer + 16*[board_info["layer"]]
      else:
        layer   = layer   + 16*[-1]

      if "layer" in board_info:
        chamber = chamber + 16*[board_info["chamber"]]
      else:
        chamber = chamber + 16*[-1]

      if "layer" in board_info:
        fpc  = fpc + [board_info["fpc_a"]]*4 + [board_info["fpc_b"]]*4 + [board_info["fpc_c"]]*4 + [board_info["fpc_d"]]*4
      else:
        fpc     = fpc     + 16*[-1]

    else:
      wire    = wire    + 16*[-1]
      layer   = layer   + 16*[-1]
      chamber = chamber + 16*[-1]
      fpc     = fpc     + 16*[-1]


  with open("unify_channel_info/"+tdc+".channel_info.txt","w") as f:
    for i in range(0,channels):
      #print("{:f}\t{:d}\t{:d}\t{:d}\t{:d}\n".format(offsets[i],chamber[i],layer[i],fpc[i],wire[i]))
      #f.write("{:f}\t{:d}\t{:d}\t{:d}\t{:d}\n".format(offsets[i],chamber[i],layer[i],fpc[i],wire[i]))
      f.write("{:f}\t{:d}\t{:d}\t{:d}\t{:d}\n".format( offsets[i], chamber[i],layer[i],fpc[i],wire[i] ))
      #print( wire[i] )
    f.close()
  

  with open("unify_channel_info/reference_channel.txt","w") as f:
    reference_channel = db.get_global_settings()["reference_channel"]
    f.write("{:d}\n".format( reference_channel ))
    f.close()

  
    
