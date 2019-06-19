#!/usr/bin/env python

def ascii_hist(data, **kwargs):

  height = kwargs.get("height", 10)
  normalized = kwargs.get("normalized", True)
  tics = kwargs.get("tics", 5)
  xdata = kwargs.get("xdata", range(0,len(data)))
  left_width = kwargs.get("left_width",10)
  top_rule = kwargs.get("top_rule", True)
  bottom_rule = kwargs.get("bottom_rule", True)

  title = kwargs.get("title", None)

  statistics = kwargs.get("statistics", True)

  import numpy as np
  ps = "#"
  xs = "-"
  ys = "|"

  bins = len(data)
  
  #matrix = np.zeros(height,bins) 
 
  a = np.array(data)
  sum = np.sum(a)
  max = np.max(a)
  if normalized and sum > 0:
    a = a/float(max)*(height)
    a = np.round(a)

  out = "\n"

  if top_rule:
    out += "_"*(left_width*2+bins)+"\n\n"
  
  if title:
    title2 = title.center(bins-10)
    title2 = "#### " + title2 + " ####"
    out += " ".rjust(left_width) + title2 + "\n\n"


  left_format = "{:d} |"
  for i in range(0,height):
    y = height -1 -i
    if normalized:
      ylabel = (height-i)/float(height)*100
      left_format = "{:.1f}% |"
      out += left_format.format(ylabel).rjust(left_width)
    else: 
      out += left_format.format(y).rjust(left_width)
    for j in range(0,bins):
      if y < a[j]:
        out += ps
      else:
        out += " "
    out += "\n"

  ## x axis
  #out += " ".rjust(left_width) + xs*bins
  #out += "\n"

  # tics  
  out += "|".rjust(left_width)
  for x in xdata:
    if x % tics == 0: 
      ## time for a tic
      out += "+"
    else:
      out += "-"
  out += "\n"

  # tics  labels
  out += " ".rjust(left_width)
 
  idle = 0
  for x in xdata:
    if idle == 0:
      if x % tics == 0: 
        ## time for a tic
        ticstr = str(x)
        idle+= len(ticstr)-1
        out += ticstr
      else:
        out += " "
    elif idle > 0:
      idle -= 1
      
  out += "\n"

  if statistics:
    vals = np.array(data)
    xvals = np.array(xdata)
    sum  = float(np.sum(vals))
    mean = 0
    stddev  = -1
    if (sum > 0):
      weights = vals/float(sum)
      mean    = np.dot(weights,xvals)
      stddev    = np.sqrt(np.dot(weights,np.power(xvals-mean,2)))
    out += "\n"
    out += " ".rjust(left_width)+"mean: "+"{:.2f}".format(mean).rjust(6) 
    out += "  stddev: "+"{:.2f}".format(stddev).rjust(6) 
    out += "\n"

  if bottom_rule:
    out += "_"*(left_width*2+bins)+"\n"


  return out
