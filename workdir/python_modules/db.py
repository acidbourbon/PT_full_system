import json
import os

root_dir   = "/workdir/db/"
setup_file = "setup.json"

def dump_db_to_root(outfile):
  dump_db_to_csv("/dev/null",export_root_file=outfile)

def dump_db_to_root_board(outfile,board_name):
  dump_db_to_csv("/dev/null",export_root_file=outfile,only_board=board_name)

def dump_db_to_csv(outfile,**kwargs):

  only_active_boards = kwargs.get("only_active_boards",False)
  only_nostandby_boards = kwargs.get("only_nostandby_boards",False)
  only_board = kwargs.get("only_board",False)   
  export_root_file = kwargs.get("export_root_file","/dev/null")

  #export_root = False
  #if export_root_file != "":
  #  export_root = True


  from ROOT import TFile, TTree, TH1, TH1F
  from array import array
  import numpy as np



  root_dump = TFile(export_root_file,"RECREATE")
  dump_tree = TTree("dump_tree","dump_tree") 
  calib_tree = TTree("calib_tree","calib_tree") 
  dummy_calib_tree = TTree("dummy_calib_tree","dummy_calib_tree") 
  dummy_tsbl_tree = TTree("dummy_tsbl_tree","dummy_tsbl_tree") 

  

  my_board_list = []
    
  if only_nostandby_boards:
    my_board_list = nostandby_board_list()
  if only_active_boards:
    my_board_list = active_board_list()
  if only_board:
    my_board_list = [ only_board ]
  else:
    my_board_list = board_list()
#     my_board_list = nostandby_board_list()
    
  col_width = 32

  with open(outfile,"w") as f:

    list_type_keys = []
    my_keys = []

    # first collect keys
    for board in my_board_list:
      print( "scanning keys of board: "+board )
      board_info = find_board_by_name(board)

      calib_ = get_calib_json_by_name(board)
      dummy_calib_ = get_calib_json_by_name(board,dummy_calib=True)

      calib = {}
      dummy_calib = {}

      for key in calib_:
        new_key = "calib_"+key
        calib[new_key] = calib_[key]
      board_info.update(calib)

      for key in dummy_calib_:
        new_key = "dummy_calib_"+key
        dummy_calib[new_key] = dummy_calib_[key]
      board_info.update(dummy_calib)


      for key in board_info:
        if not( key in my_keys):
          my_keys += [key]
          if isinstance(board_info[key],list):
            if len(board_info[key]) == 16:
              list_type_keys += [key]

    root_vals = []
    for j in range(0,len(my_keys)):
      root_vals.append(array('f',[0.]))

    # generate report 
    if len(my_keys) > 0: 
      my_keys.sort()
      line = ""
      for j in range(0,len(my_keys)):
        key = my_keys[j]
        line += str(key).ljust(col_width)+","
        dump_tree.Branch(key,root_vals[j],key)
        calib_tree.Branch(key,root_vals[j],key)
        dummy_calib_tree.Branch(key,root_vals[j],key)
        dummy_tsbl_tree.Branch(key,root_vals[j],key)
      f.write(line+"\n")

      for board in my_board_list:
        print( "dumping data of board: "+board )
        board_info = find_board_by_name(board)

        calib_ = get_calib_json_by_name(board)
        dummy_calib_ = get_calib_json_by_name(board,dummy_calib=True)
  
        calib = {}
        dummy_calib = {}
  
        for key in calib_:
          new_key = "calib_"+key
          calib[new_key] = calib_[key]
        board_info.update(calib)
  
        for key in dummy_calib_:
          new_key = "dummy_calib_"+key
          dummy_calib[new_key] = dummy_calib_[key]
        board_info.update(dummy_calib)

       
        # each channel individually
        for i in range(0,16):
          line = ""
          for j in range(0,len(my_keys)):
            key = my_keys[j]
            element = ""
            if key in board_info:
              if key in list_type_keys:
                element = board_info[key][i]
              else:
                element = board_info[key]
              if not(isinstance(element,str)):
                element = str(element)
            line += '"'+element.ljust(col_width)+'"'+","
            try:
              float_element = float(element)
            except ValueError:
              float_element = -1.
            root_vals[j][0] = float_element
          f.write(line+"\n")
          dump_tree.Fill()

        ## only for root export: ##
        ## try putting the noise scan histogram in there ##
        ## you need the above loop to have run already, to get the right combination with all other observables
        if export_root_file != "/dev/null":
          for i in range(0,16):
            for j in range(0,len(my_keys)):
              key = my_keys[j]
              ### all the other keys still need to be updated
              element = ""
              if key in board_info:
                if key in list_type_keys:
                  element = board_info[key][i]
                else:
                  element = board_info[key]
                if not(isinstance(element,str)):
                  element = str(element)
              line += '"'+element.ljust(col_width)+'"'+","
              try:
                float_element = float(element)
              except ValueError:
                float_element = -1.
              root_vals[j][0] = float_element
              
              ### now we come to the special part for the noise scan raw data

              if key == "calib_noise_scan_raw" or key == "dummy_calib_noise_scan_raw" or key == "dummy_calib_tsbl_scan_raw":
                if key in board_info:
                  hist_data = np.array(board_info[key][i])
                  #hist_sum = sum(hist_data)
                  hist_sum = 10e6
                  if hist_sum == 0:
                    hist_sum = 1000
                  hist_data = np.round(hist_data/float(hist_sum) * 100.)
                  #x=range(-15,16)
                  for l in range(0,len(hist_data)):
                    for m in range(0,int(hist_data[l])):
                      if key == "calib_noise_scan_raw":
                        x=board_info["calib_bl_range"]
                        root_vals[j][0] = x[l]
                        calib_tree.Fill()
                      elif key == "dummy_calib_noise_scan_raw":
                        x=board_info["dummy_calib_bl_range"]
                        root_vals[j][0] = x[l]
                        dummy_calib_tree.Fill()
                      elif key == "dummy_calib_tsbl_scan_raw":
                        x=board_info["dummy_calib_tsbl_range"]
                        root_vals[j][0] = x[l]
                        dummy_tsbl_tree.Fill()


             
    f.close()
    dump_tree.Write()
    calib_tree.Write()
    dummy_calib_tree.Write()
    dummy_tsbl_tree.Write()
    root_dump.Close()



def write_go4_settings_h():
  with open("/workdir/go4_settings.h","w") as f:
    f.write("//do not edit by hand, this is automatically generated/overwritten by db.py\n\n\n")

    global_settings = get_global_settings()
    for key in  global_settings:
      f.write("#define {:s} {:s}\n".format(str(key),str(global_settings[key])))

    sorted_hub_list = sorted(active_hub_list())
    sorted_tdc_list = sorted(active_tdc_list())
    f.write("#define HUBRANGE_START {:s}\n".format( str(sorted_hub_list[0]) ))
    f.write("#define HUBRANGE_STOP {:s}\n".format(  str(sorted_hub_list[-1]) ))
    f.write("#define TDCRANGE_START {:s}\n".format( str(sorted_tdc_list[0]) ))
    f.write("#define TDCRANGE_STOP {:s}\n".format(  str(sorted_tdc_list[-1]) ))
    
    f.write("\n\n// second processes in second.C:\n")
    ### // new SecondProc("Sec_0350", "TDC_0350");
    f.write("#define SECOND_PROCESS_TDCs ")
    for tdc_addr in active_tdc_list():
      tdc_int = tdc_addr.replace("0x","");
      f.write("new SecondProc(\"Sec_{:s}\", \"TDC_{:s}\");".format(tdc_int,tdc_int));

    f.write("\n\n")

    ## find tdc with the most channels
    #no_channels_list = []
    #for tdc_addr in active_tdc_list():
    #  no_channels_list += [get_tdc_json(tdc_addr)["channels"]]

    #f.write("#define CHANNELS {:d}\n".format( max(no_channels_list)  ))
      

    f.close()

def clear_t1_offsets_of_board(board_name):
  board_info = find_board_by_name(board_name)
  tdc_addr = board_info["tdc_addr"]
  channels = board_info["channels"]
  tdc_json = get_tdc_json(tdc_addr)
  for ch in channels:
    tdc_json["t1_offset"][ch] = 0
  write_tdc_json(tdc_addr,tdc_json)

def get_t1_offsets_of_board(board_name):
  board_info = find_board_by_name(board_name)
  return board_info["t1_offsets"]

def clear_t1_offsets_of_tdc(tdc_addr):
  tdc_json = get_tdc_json(str(tdc_addr))
  channels = tdc_json["channels"]
  tdc_json["t1_offset"] = [0]*channels
  write_tdc_json(str(tdc_addr),tdc_json)



def get_t1_offsets(tdc_addr):
  t1_offset = get_tdc_json(str(tdc_addr))["t1_offset"]
  return t1_offset

def get_global_settings():
  return get_setup_json()["global_settings"]


def dump(obj):
  print( json.dumps(obj,indent=2,sort_keys=True)   )


def get_setup_json():
  setup_fh = open(root_dir+setup_file,"r")
  setup    = json.load(setup_fh)
  setup_fh.close()
  return setup


def get_calib_json(calib_file,**kwargs):

  dummy_calib = kwargs.get("dummy_calib",False)
  if dummy_calib:
    calib_file = calib_file+".dummy"
  
  if os.path.exists(root_dir+calib_file):

    calib_fh = open(root_dir+calib_file,"r")
    calib    = json.load(calib_fh)
    calib_fh.close()
    return calib
  else:
    return {}


def write_setup_json(setup):
  setup_fh = open(root_dir+setup_file,"w")
  json.dump(setup,setup_fh,indent=2,sort_keys=True)
  setup_fh.close()
  write_go4_settings_h()


def write_calib_json(calib_file, calib_json,**kwargs):

  dummy_calib = kwargs.get("dummy_calib",False)
  if dummy_calib:
    calib_file = calib_file+".dummy"

  calib_fh = open(root_dir+calib_file,"w")
  json.dump(calib_json,calib_fh,indent=2,sort_keys=True)
  calib_fh.close()



def enable_board(board_name):
  update_board_json_by_name(board_name,{"active":1})

def disable_board(board_name):
  update_board_json_by_name(board_name,{"active":0})

def set_standby_board(board_name):
  update_board_json_by_name(board_name,{"standby":1})

def unset_standby_board(board_name):
  update_board_json_by_name(board_name,{"standby":0})


def find_board_by_tdc_channel(my_tdc, my_channel):
  setup = get_setup_json()
  my_connector = int(my_channel/16)+1
  return find_board_by_tdc_connector(my_tdc, my_connector)


def find_board_by_name(board_name):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board_name ==  board["name"]:
          return find_board_by_tdc_connector(tdc["addr"],board["tdc_connector"])

  return 0

def find_board_by_fpc(fpc,layer,chamber):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if chamber == board["chamber"] and layer == board["layer"]:
            if fpc == board["fpc_a"] or fpc == board["fpc_b"] or fpc == board["fpc_c"] or fpc == board["fpc_d"]:
                return board["name"]

  return 0

def get_chamber_of_board(board_name):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board_name ==  board["name"]:
          return board["chamber"]
  return 0

def get_layer_of_board(board_name):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board_name ==  board["name"]:
          return board["layer"]
  return 0

def get_fpca_of_board(board_name):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board_name ==  board["name"]:
          return board["fpc_a"]
  return 0

def get_fpcd_of_board(board_name):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board_name ==  board["name"]:
          return board["fpc_d"]
  return 0

def get_calib_json_by_name(board_name,**kwargs):
  board_info = find_board_by_name(board_name)
  calib_file = board_info["calib_file"]
  return get_calib_json(calib_file,**kwargs)
  
def write_calib_json_by_name(board_name,calib_json,**kwargs):
  board_info = find_board_by_name(board_name)
  calib_file = board_info["calib_file"]
  write_calib_json(calib_file,calib_json,**kwargs)

def update_calib_json_by_name(board_name,calib_json_update,**kwargs):
  board_info = find_board_by_name(board_name)
  calib_file = board_info["calib_file"]
  calib_json = get_calib_json(calib_file,**kwargs)
  calib_json.update(calib_json_update)
  write_calib_json(calib_file,calib_json,**kwargs)

def get_board_json_by_name(board_name):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board_name ==  board["name"]:
          return board
  return 0

def get_tdc_json_by_addr(tdc_addr):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"].lower() == tdc_addr.lower():
        return tdc
  return 0

def write_board_json_by_name(board_name,board_json):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board_name ==  board["name"]:
          for key in list(board.keys()):
            del board[key]
          board.update( board_json)
  write_setup_json(setup)
  
def update_board_json_by_name(board_name,board_json_update):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board_name ==  board["name"]:
          board.update(board_json_update)
  write_setup_json(setup)
  


### every other find_board_XXX function will eventually call this ###

def find_board_by_tdc_connector(my_tdc, my_connector):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"].lower() == my_tdc.lower():
        for board in tdc["board"]:
          conn = board["tdc_connector"]
          if my_connector == conn :
            board_defs = board.copy()
            fpc_a = -4           
            fpc_b = -3
            fpc_c = -2
            fpc_d = -1
            reverse_mapping = 0

            if( "fpc_a" in board_defs):
              fpc_a = board_defs["fpc_a"]  
            if( "fpc_b" in board_defs):
              fpc_b = board_defs["fpc_b"] 
            if( "fpc_c" in board_defs):
              fpc_c = board_defs["fpc_c"]
            if( "fpc_d" in board_defs):
              fpc_d = board_defs["fpc_d"]

            if( "reverse_mapping" in board_defs):
              reverse_mapping = board_defs["reverse_mapping"]

            wires = []

            if( reverse_mapping ):
              wires =  list(range((fpc_a+1)*4-1,fpc_a*4-1, -1)) + list(range((fpc_b+1)*4-1,fpc_b*4-1, -1)) + list(range((fpc_c+1)*4-1,fpc_c*4-1, -1)) + list(range((fpc_d+1)*4-1,fpc_d*4-1, -1)) 
            else:
              wires =  list(range(fpc_a*4,(fpc_a+1)*4)) + list(range(fpc_b*4,(fpc_b+1)*4)) + list(range(fpc_c*4,(fpc_c+1)*4)) + list(range(fpc_d*4,(fpc_d+1)*4))
           
            channels =  list(range((conn-1)*16,conn*16))
            
            t1_offsets = []
            for ch in channels:
              t1_offsets += [tdc["t1_offset"][ch]]
           
            t1_is_calibrated = 0
            if t1_offsets != [0]*16:
              t1_is_calibrated = 1
            
            baseline_is_calibrated = 0
            calib_json =  get_calib_json(board_defs["calib_file"])
            if "baselines" in calib_json:
              baseline_is_calibrated = 1
            if "ch_error" in calib_json:
              if calib_json["ch_error"] != [0]*16:
                baseline_is_calibrated = -1
            
            board_defs.update({"tdc_addr" : tdc["addr"], "hub_addr" : hub["addr"],\
            "channels": channels,\
            "wires" : wires,\
            "t1_offsets" : t1_offsets,\
            "t1_is_calibrated" : t1_is_calibrated,\
            "baseline_is_calibrated" : baseline_is_calibrated,\
            "board_chan" : list(range(0,16))
            })
            return board_defs

  return 0

def insert_board(my_tdc, board_name):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"].lower() == my_tdc.lower():
        tdc["board"] += [{ "name":board_name, "active":0 }]
  write_setup_json(setup)

def remove_board(board_name):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board_name ==  board["name"]:
          tdc["board"].remove(board)
  write_setup_json(setup)


def add_board_json(my_tdc,board_json):
  board_name = board_json["name"]
  insert_board(my_tdc,board_name)
  update_board_json_by_name(board_name,board_json)





def hub_list():
  setup = get_setup_json()
  hubs = []
  for hub in setup["hub"]:
    hubs += [hub["addr"].lower()]

  return hubs


def tdc_list():
  setup = get_setup_json()
  tdcs = []
  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      tdcs += [tdc["addr"].lower()]

  return tdcs

def active_hub_list():
  hubs = []
  ref_chan_tdc_addr = ref_chan_tdc()
  setup = get_setup_json()
  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"] == ref_chan_tdc_addr:
        hubs += [hub["addr"]]
      for board in tdc["board"]:
        if board["active"] == 1 :
          hubs += [hub["addr"]]
  return  sorted(set(hubs))

def active_tdc_list():
  ref_chan_tdc_addr = ref_chan_tdc()
  tdcs = []
  setup = get_setup_json()
  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"] == ref_chan_tdc_addr:
        tdcs += [tdc["addr"]]
      for board in tdc["board"]:
        if board["active"] == 1 :
          tdcs += [tdc["addr"]]
  return  sorted(set(tdcs))

def ref_chan_tdc():
  refchan = get_global_settings()["reference_channel"]
  return "0x{:04d}".format(int(refchan /100))
    

def board_list():
  setup = get_setup_json()
  boards = []
  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        boards += [board["name"]]

  return boards

def board_list_installed():
  setup = get_setup_json()
  boards = []
  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if "0xeee" not in tdc["addr"]:
          for board in tdc["board"]:
            boards += [board["name"]]

  return boards
def active_board_list():
  setup = get_setup_json()
  boards = []
  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board["active"] == 1 :
          boards += [board["name"]]

  return boards

def nostandby_board_list():
  setup = get_setup_json()
  boards = []
  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      for board in tdc["board"]:
        if board["standby"] == 0 :
          boards += [board["name"]]

  return boards

def calc_chip_from_channel(my_channel):
  return int((my_channel%16)/8)

def calc_connector_from_channel(my_channel):
  return int(my_channel/16)+1


def list_all_boards():
 
  print("list all boards")
  
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
    
      for board in tdc["board"]:
        print("hub:{:s}, tdc:{:s}, board:{:s}, tdc_connector:{:d}".format(hub["addr"],\
          tdc["addr"],board["name"],board["tdc_connector"]))
            

def get_tdc_json(my_tdc):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"].lower() == my_tdc.lower():
        return tdc

def write_tdc_json(my_tdc,tdc_json):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"].lower() == my_tdc.lower():
        for key in list(tdc.keys()):
          del tdc[key]
        tdc.update(tdc_json)
  write_setup_json(setup)

def update_tdc_json(my_tdc,tdc_json_update):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"].lower() == my_tdc.lower():
        tdc.update(tdc_json_update)
  write_setup_json(setup)

def insert_tdc(my_hub_addr,my_tdc_addr, name ,channels,connectors):
  setup = get_setup_json()

  for hub in setup["hub"]:
    hub_found = False
    if hub["addr"].lower() == my_hub_addr:
      hub_found = True
      break

  if (hub_found):
    hub["tdc"] += [{ "addr": my_tdc_addr , "board":[], "name": name, "channels":channels,"connectors":connectors,"t1_offset": [0] * channels }]

  write_setup_json(setup)
 
 
def remove_tdc(my_tdc):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"].lower() == my_tdc.lower():
        hub["tdc"].remove(tdc)
  write_setup_json(setup)
  
def insert_hub(my_hub_addr,my_hub_name):
  setup = get_setup_json()
  setup["hub"] += [{ "addr":my_hub_addr, "tdc":[], "name":my_hub_name }] 
  write_setup_json(setup)

def remove_hub(my_hub):
  setup = get_setup_json()

  for hub in setup["hub"]:
    if hub["addr"].lower() == my_hub.lower():
      setup["hub"].remove(hub)
  write_setup_json(setup)
