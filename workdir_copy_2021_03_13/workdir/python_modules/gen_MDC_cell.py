#!/usr/bin/env python3

import numpy as np


import sys

def gen_MDC_cell(**kwargs):
  
  ### feed the function with values in SI units, i.e. meters and volts
  
  ### if no arguments are given, the function will generate a straight (0deg) MDC I cell at -1750 V

  sense_angle_deg = float(kwargs.get("sense_angle_deg",0.))

  layer_pitch       = 1e2*float(kwargs.get("layer_pitch"       ,2.5e-3 ))
  cathode_pitch     = 1e2*float(kwargs.get("cathode_pitch"     ,2e-3  ))
  sense_field_pitch = 1e2*float(kwargs.get("sense_field_pitch" ,2.5e-3  ))


  field_wire_rad = 1e2*float(kwargs.get("field_wire_rad"       , 40e-6 ))
  cath_wire_rad  = 1e2*float(kwargs.get("cath_wire_rad"        , 40e-6 ))
  sense_wire_rad = 1e2*float(kwargs.get("sense_wire_rad"       , 10e-6 ))

  v_cath  = float(kwargs.get("v_cath"      ,-1750))  # cathode voltage
  v_field = float(kwargs.get("v_field"     ,v_cath)) # field wire voltage
  v_sense = float(kwargs.get("v_sense"     ,0.    )) # sense wire voltage

  zpitch = layer_pitch
  xpitch = cathode_pitch
  ypitch = sense_field_pitch/np.cos(sense_angle_deg/360.*np.pi*2) # sense/field wire pitch rotated


  sim_vol_xsize = 1e2*float(kwargs.get("sim_vol_xsize",30e-3)) # along the sense wire
  sim_vol_ysize = 1e2*float(kwargs.get("sim_vol_ysize",30e-3/np.cos(sense_angle_deg/360.*np.pi*2))) # along the cathode wires
  sim_vol_zsize = 1e2*float(kwargs.get("sim_vol_zsize",30e-3)) # in layer stacking direction

  cath_conductor  = "conductor-1"
  field_conductor = "conductor-1"
  sense_conductor = "conductor-2"

  sense_direction = "%f %f %f" % (1, np.tan(sense_angle_deg/360.*np.pi*2), 0)
  field_direction = sense_direction



  with open("CELL.txt","w") as f:

    ## section header
    print(  "*****************CELL***********************" , file=f)
    print(  "* generating MDC  geometry at {:} V (field) / {:} V (cathodes)".format(v_field,v_cath) , file=f)
    print(  "&CELL" , file=f)
    print(  "solids" , file=f)



    print(  "*** generate sense wires ***" , file=f)
    x=0
    for y in np.arange(0,sim_vol_ysize/2.,ypitch*2) :
      for z in np.arange(0,sim_vol_zsize/2.,zpitch*2) :
        y_bar = y
        if ( (z/zpitch)%4 ):
          y_bar = y+ypitch
        print(  "wire  centre {:} {:} {:} ...".format(x,y_bar,z) , file=f)
        print(  "      direction "+sense_direction+" ..." , file=f)
        print(  "      radius {:} ... ".format(sense_wire_rad) , file=f)
        print(  "      half-length {:} ...".format(sim_vol_xsize/2.) , file=f)
        print(  "      "+sense_conductor+" ..." , file=f)
        if( y_bar == 0 and z == 0):
          print(  "      label S ..." , file=f)
        if( y_bar == ypitch and z == zpitch*2):
          print(  "      label T ..." , file=f)
        print(  "      voltage {:}".format(v_sense) , file=f)
        if (y_bar > 0):
          print(  "wire  centre {:} {:} {:} ...".format(x,-y_bar,z) , file=f)
          print(  "      direction "+sense_direction+" ..." , file=f)
          print(  "      radius {:} ... ".format(sense_wire_rad) , file=f)
          print(  "      half-length {:} ...".format(sim_vol_xsize/2.) , file=f)
          print(  "      "+sense_conductor+" ..." , file=f)
          print(  "      voltage {:}".format(v_sense) , file=f)
        if (z > 0):
          print(  "wire  centre {:} {:} {:} ...".format(x,y_bar,-z) , file=f)
          print(  "      direction "+sense_direction+" ..." , file=f)
          print(  "      radius {:} ... ".format(sense_wire_rad) , file=f)
          print(  "      half-length {:} ...".format(sim_vol_xsize/2.) , file=f)
          print(  "      "+sense_conductor+" ..." , file=f)
          print(  "      voltage {:}".format(v_sense) , file=f)
        if (y_bar > 0 and z > 0):
          print(  "wire  centre {:} {:} {:} ...".format(x,-y_bar,-z) , file=f)
          print(  "      direction "+sense_direction+" ..." , file=f)
          print(  "      radius {:} ... ".format(sense_wire_rad) , file=f)
          print(  "      half-length {:} ...".format(sim_vol_xsize/2.) , file=f)
          print(  "      "+sense_conductor+" ..." , file=f)
          print(  "      voltage {:}".format(v_sense) , file=f)
      
    print(  "*** generate field wires ***" , file=f)
    x=0
    for y in np.arange(0,sim_vol_ysize/2.,ypitch*2) :
      for z in np.arange(0,sim_vol_zsize/2.,zpitch*2) :
        y_bar = y
        if ( (z/zpitch)%4 == 0):
          y_bar = y+ypitch
        print(  "wire  centre {:} {:} {:} ...".format(x,y_bar,z) , file=f)
        print(  "      direction "+field_direction+" ..." , file=f)
        print(  "      radius {:} ... ".format(field_wire_rad) , file=f)
        print(  "      half-length {:} ...".format(sim_vol_xsize/2.) , file=f)
        print(  "      "+field_conductor+" ..." , file=f)
        print(  "      voltage {:}".format(v_field) , file=f)
        if (y_bar > 0):
          print(  "wire  centre {:} {:} {:} ...".format(x,-y_bar,z) , file=f)
          print(  "      direction "+field_direction+" ..." , file=f)
          print(  "      radius {:} ... ".format(field_wire_rad) , file=f)
          print(  "      half-length {:} ...".format(sim_vol_xsize/2.) , file=f)
          print(  "      "+field_conductor+" ..." , file=f)
          print(  "      voltage {:}".format(v_field) , file=f)
        if (z > 0):
          print(  "wire  centre {:} {:} {:} ...".format(x,y_bar,-z) , file=f)
          print(  "      direction "+field_direction+" ..." , file=f)
          print(  "      radius {:} ... ".format(field_wire_rad) , file=f)
          print(  "      half-length {:} ...".format(sim_vol_xsize/2.) , file=f)
          print(  "      "+field_conductor+" ..." , file=f)
          print(  "      voltage {:}".format(v_field) , file=f)
        if (y_bar > 0 and z > 0):
          print(  "wire  centre {:} {:} {:} ...".format(x,-y_bar,-z) , file=f)
          print(  "      direction "+field_direction+" ..." , file=f)
          print(  "      radius {:} ... ".format(field_wire_rad) , file=f)
          print(  "      half-length {:} ...".format(sim_vol_xsize/2.) , file=f)
          print(  "      "+field_conductor+" ..." , file=f)
          print(  "      voltage {:}".format(v_field) , file=f)
      
      
    print(  "*** generate cathode wires ***" , file=f)
    y=0
    for x in np.arange(xpitch/2.,sim_vol_xsize/2.,xpitch) :
      for z in np.arange(zpitch,sim_vol_zsize/2.,zpitch*2) :
        print(  "wire  centre {:} {:} {:} ...".format(x,y,z) , file=f)
        print(  "      direction 0 1 0 ..." , file=f)
        print(  "      radius {:} ... ".format(cath_wire_rad) , file=f)
        print(  "      half-length {:} ...".format(sim_vol_ysize/2.) , file=f)
        print(  "      "+cath_conductor+" ..." , file=f)
        print(  "      voltage {:}".format(v_cath) , file=f)
        if (x > 0):
          print(  "wire  centre {:} {:} {:} ...".format(-x,y,z) , file=f)
          print(  "      direction 0 1 0 ..." , file=f)
          print(  "      radius {:} ... ".format(cath_wire_rad) , file=f)
          print(  "      half-length {:} ...".format(sim_vol_ysize/2.) , file=f)
          print(  "      "+cath_conductor+" ..." , file=f)
          print(  "      voltage {:}".format(v_cath) , file=f)
        if (z > 0):
          print(  "wire  centre {:} {:} {:} ...".format(x,y,-z) , file=f)
          print(  "      direction 0 1 0 ..." , file=f)
          print(  "      radius {:} ... ".format(cath_wire_rad) , file=f)
          print(  "      half-length {:} ...".format(sim_vol_ysize/2.) , file=f)
          print(  "      "+cath_conductor+" ..." , file=f)
          print(  "      voltage {:}".format(v_cath) , file=f)
        if (x > 0 and z > 0):
          print(  "wire  centre {:} {:} {:} ...".format(-x,y,-z) , file=f)
          print(  "      direction 0 1 0 ..." , file=f)
          print(  "      radius {:} ... ".format(cath_wire_rad) , file=f)
          print(  "      half-length {:} ...".format(sim_vol_ysize/2.) , file=f)
          print(  "      "+cath_conductor+" ..." , file=f)
          print(  "      voltage {:}".format(v_cath) , file=f)

    print(  " " , file=f)

    f.close()




if __name__=='__main__':
    gen_MDC_cell( **dict(arg.split('=') for arg in sys.argv[1:])) # kwargs
