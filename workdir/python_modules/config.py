#!/usr/bin/env python3

# ------ standart Python classes ---------

import os
import datetime
import sys, tty, termios
#import json
#from numpy import *
#from glob import glob

from extras import *


echarge = 1.602176634*10**(-19)  #elementary charge [C]


# --------------------------- Looking for Results directory and create it if missing
ResultsPath=os.path.split(os.path.realpath(__file__))[0].replace("/Devices","/Results")
if not os.path.exists(ResultsPath):
	printc("Creating Results directory... %s"%ResultsPath,"blue",0)
	os.system("mkdir %s"%ResultsPath)

# --------------------------- Looking for Results directory and create it if missing
ReportsPath=os.path.split(os.path.realpath(__file__))[0].replace("/Devices","/Reports")
if not os.path.exists(ReportsPath):
	printc("Creating Reports directory... %s"%ReportsPath,"blue",0)
	os.system("mkdir %s"%ReportsPath)


ReportPatternFile=os.path.split(os.path.realpath(__file__))[0].replace("/Devices","/tmpl_sumreport.tex")


