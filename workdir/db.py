import json
import os

root_dir   = "./db/"
setup_file = "setup.json"



def get_t1_offsets(tdc_addr):
  t1_offset = get_tdc_json(str(tdc_addr))["t1_offset"]
  return t1_offset


def dump(obj):
  print json.dumps(obj,indent=2)  


def get_setup_json():
  setup_fh = open(root_dir+setup_file,"r")
  setup    = json.load(setup_fh)
  setup_fh.close()
  return setup


def get_calib_json(calib_file):
  
  if os.path.exists(root_dir+calib_file):

    calib_fh = open(root_dir+calib_file,"r")
    calib    = json.load(calib_fh)
    calib_fh.close()
    return calib
  else:
    return {}


def write_setup_json(setup):
  setup_fh = open(root_dir+setup_file,"w")
  json.dump(setup,setup_fh,indent=2)
  setup_fh.close()


def write_calib_json(calib_file, calib_json):
  calib_fh = open(root_dir+calib_file,"w")
  json.dump(calib_json,calib_fh,indent=2)
  calib_fh.close()



def enable_board(board_name):
  update_board_json_by_name(board_name,{"active":1})

def disable_board(board_name):
  update_board_json_by_name(board_name,{"active":0})


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


def get_calib_json_by_name(board_name):
  board_info = find_board_by_name(board_name)
  calib_file = board_info["calib_file"]
  return get_calib_json(calib_file)
  
def write_calib_json_by_name(board_name,calib_json):
  board_info = find_board_by_name(board_name)
  calib_file = board_info["calib_file"]
  write_calib_json(calib_file,calib_json)

def update_calib_json_by_name(board_name,calib_json_update):
  board_info = find_board_by_name(board_name)
  calib_file = board_info["calib_file"]
  calib_json = get_calib_json(calib_file)
  calib_json.update(calib_json_update)
  write_calib_json(calib_file,calib_json)

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
          for key in board.keys():
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
              wires = [ range((fpc_a+1)*4-1,fpc_a*4-1, -1) + range((fpc_b+1)*4-1,fpc_b*4-1, -1) + range((fpc_c+1)*4-1,fpc_c*4-1, -1) + range((fpc_d+1)*4-1,fpc_d*4-1, -1) ]
            else:
              wires = [ range(fpc_a*4,(fpc_a+1)*4) + range(fpc_b*4,(fpc_b+1)*4) + range(fpc_c*4,(fpc_c+1)*4) + range(fpc_d*4,(fpc_d+1)*4) ]
            
            
            board_defs.update({"tdc_addr" : tdc["addr"], "hub_addr" : hub["addr"],\
            "channels": range((conn-1)*16,conn*16),\
            "wires" : wires,\
            })
            return board_defs

  return 0

def insert_board(my_tdc, board_name):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"].lower() == my_tdc.lower():
        tdc["board"] += [{ "name":board_name }]
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







def tdc_list():
  setup = get_setup_json()
  tdcs = []
  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      tdcs += [tdc["addr"].lower()]

  return tdcs

def board_list():
  setup = get_setup_json()
  boards = []
  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
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
        for key in tdc.keys():
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
    if hub["addr"].lower() == my_hub_addr:
      hub["tdc"] += [{ "addr": my_tdc_addr , "name": name, "channels":channels,"connectors":connectors,"t1_offset": [0] * channels }]
  write_setup_json(setup)
  
def remove_tdc(my_tdc):
  setup = get_setup_json()

  for hub in setup["hub"]:
    for tdc in hub["tdc"]:
      if tdc["addr"].lower() == my_tdc.lower():
        hub["tdc"].remove(tdc)
  write_setup_json(setup)
  
