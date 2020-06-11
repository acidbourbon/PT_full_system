#!/usr/bin/env python

import json
#from jsonpath_ng import jsonpath, parse

def dump(obj):
  print json.dumps(obj,indent=2)  




setup_fh = open("setup.json","r")
setup    = json.load(setup_fh)
setup_fh.close()

print("read setup.json:")
#print json.dumps(setup,indent=2)

print
print

#print setup["hubs"][0]

#print("query")
#dump( [m.value for m in parse('$..tdc[*]').find(setup)] )  

print("list all boards")
#dump( [m.value for m in parse('$..board[*]').find(setup)] )  

for hub in setup["hub"]:
  for tdc in hub["tdc"]:
    for board in tdc["board"]:
      print("hub:{:s}, tdc:{:s}, board:{:s}, tdc_connector:{:d}".format(hub["addr"],\
        tdc["addr"],board["name"],board["tdc_connector"]))
            



setup_fh = open("setup.json","w")
json.dump(setup,setup_fh,indent=2)
setup_fh.close()
