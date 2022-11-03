#!/usr/bin/env python3
#in FST docker container : after start of docker isntall: pip install scipy==1.1.0
# ------ standart Python classes ---------

import os
import time
import sys, tty, termios
import threading
#import json
from numpy import *
#from glob import glob

# ------ PANDa specified classes ---------
sys.path.append(os.path.split(os.path.realpath(__file__))[0]+"/Devices")

from config import *

# -- laboratory equipment --
from signal_generator import signal_generator

# -- Other --
from TrbDataReader import TrbDataReader
from PANDAmux import PANDAinjectors
from PANDAfeb import PANDAfeb
import pasttrec_ctrl as pasttrec_ctrl

from measSCurve import measSCurve
from measBaseline import measBaseline
from measDacs import measDacs
from measTOTs import measTOTs

#os.system("clear")

# --- Charge Injectors configuration ----------

Injectors = PANDAinjectors()

# --- FEB and data reader configuration ----------
measure_board_name="4000"
# PASTTREC ASIC parameters:
pt_pktime = 10
pt_gain = 1
pt_threshold_default = 20

BranchCfg = {}

#Configure FEB boards connected to the system BranchCfg[testBranch]={"InjAddr":7,"UserID":"B000"}
BranchCfg[0] = {"InjAddr":0,"UserID":"socketTest"} 
#BranchCfg[1] = {"InjAddr":1,"UserID":"E063"} 
#BranchCfg[2] = {"InjAddr":2,"UserID":"TXE002"} 
#BranchCfg[3] = {"InjAddr":3,"UserID":"TXE003"} 
#BranchCfg[4] = {"InjAddr":4,"UserID":"TXE004"} 
#BranchCfg[5] = {"InjAddr":5,"UserID":"TXE005"} 
#BranchCfg[6] = {"InjAddr":6,"UserID":"TXE006"} 
#BranchCfg[7] = {"InjAddr":7,"UserID":"TXE007"}

#list of all active branches
testBranches = list(BranchCfg.keys())

DataReader = TrbDataReader(testBranches)

Febs = {}
for i in testBranches:
	Febs[i] = PANDAfeb(i,BranchCfg[i]["UserID"])
	for qinf in Injectors.InjObjects[BranchCfg[i]["InjAddr"]].qinFactors: 
		Febs[i].convFactors.append(qinf * Injectors.globConvFactor) #conversion factor will be used for all measurements in this sesion and stored with measurements data
	

# ---- initializing laboratory equipment ----

gen = signal_generator("ip:192.168.0.197:5025")
gen.initialize((1,2))


# ---- creating mesurements classes objects ----

#sCurveMeas = measSCurve(gen,DataReader,Injectors,Febs)
baseMeas = measBaseline(gen,DataReader,Injectors,Febs)
#dacsMeas = measDacs(gen,DataReader,Injectors,Febs)
totsMeas = measTOTs(gen,DataReader,Injectors,Febs)

#------------------------------------------------------------------------------------------------------
#   Some functions for better organization
#------------------------------------------------------------------------------------------------------

# ---------------- Set indicators
def setStatusIndicator(sOK="injectors OK",sERR="err"):
	status={0:sERR,1:sOK}
	for feb in Febs: 
		Injectors.InjObjects[BranchCfg[feb]["InjAddr"]].setIndicator(status[int(Febs[feb].FEBok)])

# ---------------- Checking status of Febs and remove bad boards from further mesurements
def removeBadFEBs():
	delkeys=[]
	for feb in Febs: 
		if not Febs[feb].FEBok:
			Febs[feb].log("FEB: %s (Branch: %d) removing from further testing list!"%(Febs[feb].userID,feb),"red",0)
			delkeys.append(feb)
	setStatusIndicator()
	for dk in delkeys: del Febs[dk]
	printc("Active FEBs: %s"%(str(list(Febs.keys()))),"blue",0)


def goBackground(f,*a):
	thread = threading.Thread(target=f, args=a)
	thread.start()

if __name__=="__main__":
	#------------------------------------------------------------------------------------------------------
	#------------------------------------------------------------------------------------------------------
	#-----------------------------------     Measurements Procedure   -------------------------------------
	#------------------------------------------------------------------------------------------------------
	#------------------------------------------------------------------------------------------------------
	removeBadFEBs()
	
	#sys.exit()
	#gen.set_display_state(False)


	#ChipConfs = ["1mV20ns","2mV15ns","2mV20ns","4mV15ns","4mV20ns"]
	ChipConfs = ["PT{}mV{}ns".format(pt_gain,pt_pktime) ]



	'''
	# --------------------------      DACs test         ----------------------------
	#Measurements of the DACs quality will be done only at highest gain to obtain as good precision as possible
	# ------------------------------------------------------------------------------
	ConfName = "4mV20ns"
	MeasName = "%s"%ConfName
	# -- initial configuration
	for feb in Febs: Febs[feb].setTypicalConfiguration(ConfName)
	#Baseline and Threshold setting skipped - will be set during measurements
	# -- Measurements and fitting - Base
	dacsMeas.runBaselineDacTest(MeasName)
	for feb in Febs: Febs[feb].saveData()  #saving data to files...
	dacsMeas.fitBaselineDacData(MeasName)
	for feb in Febs: Febs[feb].saveData()  #saving data to files...
	# -- Measurements and fitting - Th
	
	dacsMeas.runThresholdDacTest(MeasName)
	for feb in Febs: Febs[feb].saveData()  #saving data to files...
	dacsMeas.fitThresholdDacData(MeasName)
	for feb in Febs: Febs[feb].saveData()  #saving data to files...
	
	# -- Plotting ...
	dacsMeas.plotBaselineDacsCurves(MeasName)
	dacsMeas.plotThresholdDacsCurves(MeasName)
	# ------------------------------------------------------------------------------
	'''
	
	
	'''
	# --------------------------  Baseline measurements ----------------------------
	# 
	# ------------------------------------------------------------------------------
	for ConfName in ChipConfs:
		MeasName = "%s"%ConfName
		# -- initial configuration
		for feb in Febs: Febs[feb].setTypicalConfiguration(ConfName)
		#Baseline and Threshold setting skipped - will be set during measurements
		# -- Measurements and fitting
		baseMeas.runBaselineSimple(MeasName)
		for feb in Febs: Febs[feb].saveData()  #saving data to files...
		baseMeas.fitBaselineData(MeasName)
		for feb in Febs: Febs[feb].saveData()  #saving data to files...
		# -- Plotting....
		baseMeas.plotBaselineDetails(MeasName)
		# -- Removing Bad Febs
		removeBadFEBs()
	#plot comparison - for all configurations
	baseMeas.plotBaselineParams()
	
	#Leaving Baselines in last configuration - centered
	#baselines = baseMeas.getBaselineSettings(ConfName,"Center")
	#printdict(baselines)
	#for feb in Febs: Febs[feb].setBaselines(baselines[feb])
	# ------------------------------------------------------------------------------
	
	'''
	
	
	
	'''
	# -------------------------  Threshold scan measurements -----------------------
	# 
	# ------------------------------------------------------------------------------
	for ConfName in ChipConfs:
		MeasName = "%s"%ConfName
		# -- initial configuration
		for feb in Febs: Febs[feb].setTypicalConfiguration(ConfName)
		baselines = baseMeas.getBaselineSettings(MeasName,"High")
		#printdict(baselines)
		for feb in Febs: Febs[feb].setBaselines(baselines[feb])
		#Threshold setting skipped - will be set during measurements
		# -- Measurements and fitting
		baseMeas.runThresholdScan(MeasName)
		for feb in Febs: Febs[feb].saveData()  #saving data to files...
		baseMeas.fitThresholdScanData(MeasName)
		for feb in Febs: Febs[feb].saveData()  #saving data to files...
		# -- Plotting....
		baseMeas.plotThresholdScanParamsCompare(MeasName)
	#plot comparison - for all configurations
	baseMeas.plotThresholdScanParams()

	# ------------------------------------------------------------------------------
	'''
	
	
	
	
	'''
	# ----------------------------   Channels checking   ---------------------------
	# 
	# ------------------------------------------------------------------------------
	ConfName = "4mV20ns"
	MeasName = "%s"%ConfName
	# -- initial configuration
	for feb in Febs: Febs[feb].setTypicalConfiguration(ConfName)
	for feb in Febs: Febs[feb].setThreshold(16)
	baselines = baseMeas.getBaselineSettings(MeasName,"Center")
	for feb in Febs: Febs[feb].setBaselines(baselines[feb])
	# -- checking...
	sCurveMeas.runQuickChannelsTest()
	for feb in Febs: Febs[feb].saveData()  #saving data to files...
	#removing boards with bad channels from testing
	removeBadFEBs()
	# ------------------------------------------------------------------------------
	'''
	
	
	
	'''
	# ---------------------------- S-curve measurements  ---------------------------
	# 
	# ------------------------------------------------------------------------------
	Thresholds = list(range(26))
	for ConfName in ChipConfs:
		MeasName = "%s"%ConfName
		# -- initial configuration
		for feb in Febs: Febs[feb].setTypicalConfiguration(ConfName)
		baselines = baseMeas.getBaselineSettings(MeasName,"Center")
		printdict(baselines)
		for feb in Febs: Febs[feb].setBaselines(baselines[feb])
		# -- Threshold Scan ...
		for th in Thresholds:
			MeasName = "%sTh%03d"%(ConfName,th)
			for feb in Febs: Febs[feb].setThreshold(th)
			# -- Measurements and fitting
			sCurveMeas.runScurveScan(MeasName) #,[0]
			for feb in Febs: Febs[feb].saveData()  #saving data to files...
			sCurveMeas.fitScurveData(MeasName)
			for feb in Febs: Febs[feb].saveData()  #saving data to files...
			# -- Plotting ...
			sCurveMeas.plotScurveDetails(MeasName)
			#sCurveMeas.plotFittedCurves(MeasName)
		# -- Plotting comparison for one selected Th
		sCurveMeas.plotScurveParamsCompare("%sTh%03d"%(ConfName,16))
		# -- Gain calculations and plotting
		sCurveMeas.fitGainData("%sTh0[0-2]"%ConfName,"%sGain"%ConfName)
		for feb in Febs: Febs[feb].saveData()  #saving data to files...
		sCurveMeas.plotGainCurves("%sGain"%ConfName)
	# -- Plotting all configuration summary - Gain and other params
	sCurveMeas.plotGainParams(["%sGain"%ConfName for ConfName in ChipConfs])
	sCurveMeas.plotScurveParams("Th008","Th008")
	sCurveMeas.plotScurveParams("Th016","Th016")
	# ------------------------------------------------------------------------------
	'''
	
	
	
	
	
	# ---------------------------- TOT Scan measurements  ---------------------------
	# 
	# ------------------------------------------------------------------------------
	#Thresholds = [6, 8, 10, 12, 16, 20]
	Thresholds = [ 15 ]	
	Gains = [ 4  ]	
	for ConfName in ChipConfs:
		MeasName = "%s"%ConfName
		# -- initial configuration
		#for feb in Febs: Febs[feb].setTypicalConfiguration(ConfName)
		pasttrec_ctrl.init_board_by_name(measure_board_name,pt_pktime ,pt_gain,pt_threshold_default)
		#baselines = baseMeas.getBaselineSettings(MeasName,"Center")
		#printdict(baselines)
		#for feb in Febs: Febs[feb].setBaselines(baselines[feb])
		# -- Threshold Scan ...
		for ga in Gains:		
			pasttrec_ctrl.init_board_by_name(measure_board_name,pt_pktime ,ga,pt_threshold_default)
			for th in Thresholds:
				MeasName = "%sGai%01dTh%03d"%(ConfName,ga,th)
				pasttrec_ctrl.set_threshold_for_board_by_name(measure_board_name,th)
				# -- Measurements and fitting
				totsMeas.runTOTsScan(MeasName) #,[0]
				for feb in Febs: Febs[feb].saveData()  #saving data to files...
				totsMeas.fitTOTsData(MeasName)
				for feb in Febs: Febs[feb].saveData()  #saving data to files...
				# -- Plotting ...
				totsMeas.plotTOTsCurves(MeasName)
	# ------------------------------------------------------------------------------
	



	# ------------------------------------------------------------------------------
	# ------------------------- End of Measurements Procedure -------------------------------
	# ------------------------------------------------------------------------------
	
	
	
	setStatusIndicator("ok","err")
	printc("Measurements finished: %s\n"%(time.strftime("%d.%m.%Y %H:%M:%S")),"blue",0)
	for feb in Febs: Febs[feb].log("Measurements finished: %s\n"%(time.strftime("%d.%m.%Y %H:%M:%S")),"blue",0,False)
	
	
	
	Injectors.closeConnection()
