#!/usr/bin/env python3


##################################################
##     generate avalanche impulse response      ##
##################################################






import numpy as np
from sigproc_kit import *



def avalanche_current(time,**kwargs):
  
  # elementary charge
  e      = 1.602e-19

  # drift chamber parameters in SI units
  U      = kwargs.get("U"      ,1600     )    # voltage difference between anode and cathode
  ra     = kwargs.get("ra"     ,10e-6    )    # wire radius
  rb     = kwargs.get("rb"     ,2.5e-3   )    # cathode tube radius (rough estimation of cell radius)
  r0     = kwargs.get("r0"     ,11e-6    )    # one mean free path length in the detector gas
  mu     = kwargs.get("mu"     ,1.7e-4   )    # ion mobility in detector gas
  idelay = kwargs.get("idelay" ,10e-9    )    # pulse starts after <idelay> seconds
  gain   = kwargs.get("gain"   ,1.6e5    )    # gain = avalanche charge amplification
  Q0     = kwargs.get("Q0"     ,1*e*gain )    # total pulse charge
  
  t0     = r0**2*np.log(rb/ra)/(2*mu*U)
  
  #print(kwargs)


  # generate the impulse response to a single electron after the gas amplification

  sig_y = np.zeros(len(time))

  ## this calculates the current directly
  #i = Q0/(2*np.log(rb/ra))*1/((time-idelay)+t0)*(time>idelay)

  ## calculate the charge and then differentiate, preserves total charge better:
  q   = Q0/(2*np.log(rb/ra))*(np.log(1e-20+ ((time-idelay)+t0)*(time>idelay)  )-np.log(t0))*(time>idelay)
  
  delta_t = time[1]-time[0]
  i   = np.diff(q)/delta_t
  result = np.empty_like(time)
  result[:1] = 0
  result[1:] = i
  
  #print(i)

  return result


def export_avalanche_current_ir():

  sample_width=2e-6
  delta_t= 0.1e-9
  samples = int(sample_width/delta_t)

  target_x = np.linspace(0,sample_width,samples)


  i = avalanche_current(target_x)


  write_csv("avalanche_current_ir.csv",target_x,i)

  plot = True

  if plot:
    import matplotlib.pyplot as plt
    
    plt.plot(target_x,i, label="avalanche impulse response")
    
    plt.legend() # order a legend.
    plt.show()
