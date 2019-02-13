import json

setup_file = "db/setup.json"


def dump(obj):
  print json.dumps(obj,indent=2)  


def get_setup_json():
  setup_fh = open(setup_file,"r")
  setup    = json.load(setup_fh)
  setup_fh.close()
  return setup


def write_setup_json(setup):
  setup_fh = open(setup_file,"w")
  json.dump(setup,setup_fh,indent=2)
  setup_fh.close()


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
            board_defs.update({"tdc_addr" : tdc["addr"], "channels": range((conn-1)*16,conn*16)   })
            return board_defs

  return 0





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
            



