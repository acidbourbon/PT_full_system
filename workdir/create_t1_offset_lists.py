#!/usr/bin/env python

import db

tdc_list = db.tdc_list();

for tdc in tdc_list:
  offsets = db.get_t1_offsets(tdc)
  with open(tdc+".t1_offsets.txt","w") as f:
    for offset in offsets:
      f.write("{:f}\n".format(offset))
    f.close()
    
