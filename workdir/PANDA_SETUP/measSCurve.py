#!/usr/bin/env python3

# ------ standart Python classes ---------

import json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from cycler import cycler
import sys
import os
from numpy import *
from scipy import stats
import scipy.optimize as opt
import scipy.special as spec
import re

from glob import glob

sys.path.append(os.path.split(os.path.realpath(__file__))[0]+"/Devices")

from config import *


plotCycler = cycler(color=["#FF0000","#00FF00","#0000FF","#FFFF00","#993300","#339900","#0288d1","#fbc02d",
													 "#f06292","#c0ca33","#4db6ac","#ff7043","#ab47bc","#795548","#90a4ae","#000000"])

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class measSCurve():
	#set font size of plot
	plt.rc('lines', linewidth=1, markersize=2)
	plt.rc('font', size=8)
	plt.rc('axes', prop_cycle=plotCycler)
	#MeasID will be added to Meas name for better measurements type recognizing
	measSCurveID="SCurve_" 
	
	
	#--------------- ----------------------
	#        INIT and general functions and private
	#--------------------------------------
	def __init__(self,gen,DataReader,Injectors,Febs):
		self.gen = gen
		self.DataReader = DataReader
		self.Injectors = Injectors
		self.Febs = Febs


	#Function returns True if All active FEB's give counts over threshold
	def countsIsOverTh(self,febCounts,injCh,th=5000):
		for feb in self.Febs:
			aAsics = self.Febs[feb].activeAsics
			if (febCounts[feb][injCh]<th and 0 in aAsics) or (febCounts[feb][injCh+8]<th and 1 in aAsics): return False
		return True


	#Function returns True if All active FEB's give counts below threshold
	def countsIsBelowTh(self,febCounts,injCh,th=1):
		for feb in self.Febs:
			aAsics = self.Febs[feb].activeAsics
			if (febCounts[feb][injCh]>=th and 0 in aAsics) or (febCounts[feb][injCh+8]>=th and 1 in aAsics): return False
		return True
	
	
	#Function search for measID type measurements and returns dictionary of lists {feb1:[meas1,meas2....],feb2:[meas1,meas2....]}
	#Optional argument measNames can select specified measurements using regular expresion of list of it
	#When measNames is None all mached measurements will be returned
	########################################################################################################
	def selectedMeasurements(self,measID,measNames=None):
		measAll={}
		for feb in self.Febs:
			measAll[feb]=[]
			for key in self.Febs[feb].measData:
				if measID.strip("_") == key.split("_")[0]: measAll[feb].append(key)
			measAll[feb] = sorted(measAll[feb])
		if measNames == None:
			return measAll
		else:
			if type(measNames) == str: measNames=[measNames]
			filterMeas={}
			for feb in self.Febs:
				filterMeas[feb]=[]
				for regexp in measNames:
					r = re.compile("[\w]{0,25}"+regexp)
					for meas in list(filter(r.match, measAll[feb])):
						if not meas in filterMeas[feb]: filterMeas[feb].append(meas)
				filterMeas[feb] = sorted(filterMeas[feb])
			return filterMeas
		
		
	#--------------- ----------------------
	#        Measurements Functions
	#--------------------------------------

#Function run Quick channels test, checks if counts appears when amplitude will be set to high value
	########################################################################################################
	def runQuickChannelsTest(self,injChns=None):
		status = True
		stime = datetime.datetime.now() 
		printc("Quick channels test for FEBs: %s started at: %s"%(str(list(self.Febs.keys())),stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0)
		for feb in self.Febs: self.Febs[feb].log("Quick channels test started at: %s"%(stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0,False)
		
		meas_time=0.5
		freq = 600.0e3
		amp=0.05
		
		if injChns == None: injChns = list(range(8))
		
		self.gen.set_frequency((1,2),freq)
		self.gen.set_amplitude((1,2),amp)
		self.gen.set_output_state((1,2),True)
			
		for feb in self.Febs: self.Febs[feb].measData["FebInfo"]["QuickChannelsTestStatus"]=[1]*16
		
		for ch in injChns:
				self.Injectors.setActiveChannel(ch)
				printc("Charge injected to channels: %d and %d"%(ch,ch+8),"purple",0)
				for feb in self.Febs: self.Febs[feb].log("Charge injected to channels: %d and %d"%(ch,ch+8),"purple",0,False)
				
				amp=0.05
				scanState = 0
				
				while(1):
					self.gen.set_amplitude((1,2),amp)
					time.sleep(1.0)
					self.gen.set_amplitude((1,2),amp)
					time.sleep(1.0)
					febCounts = self.DataReader.getCounts(meas_time)
					
					txt="A: %0.3f[V]  "%(round(amp,3))
					for feb in self.Febs: 
						txt+="%d:[%6d,%6d] "%(feb,febCounts[feb][ch],febCounts[feb][ch+8])
						self.Febs[feb].log("A: %0.3f[V] [%6d,%6d]  [counts]"%(round(amp,3),febCounts[feb][ch],febCounts[feb][ch+8]),"green",1,False)
					printc(txt+" [counts]","green",1)
					
					if scanState == 0: #read counts at low amplitude all channels should report 0 counts
						#----------------------------------------
						for feb in self.Febs:
							aAsics = self.Febs[feb].activeAsics
							if (febCounts[feb][ch]>1000 and 0 in aAsics): 
							#if febCounts[feb][ch]>1000 or febCounts[feb][ch+8]>1000: 
								self.Febs[feb].FEBok = False 
								self.Febs[feb].log("Channel: %d gives unexpected response!"%(ch),"red",1)
								status = False
							if (febCounts[feb][ch+8]>1000 and 1 in aAsics): 
							#if febCounts[feb][ch]>1000 or febCounts[feb][ch+8]>1000: 
								self.Febs[feb].FEBok = False 
								self.Febs[feb].log("Channel: %d gives unexpected response!"%(ch+8),"red",1)
								status = False
							if febCounts[feb][ch]>1000: self.Febs[feb].measData["FebInfo"]["QuickChannelsTestStatus"][ch] = 0
							if febCounts[feb][ch+8]>1000: self.Febs[feb].measData["FebInfo"]["QuickChannelsTestStatus"][ch+8] = 0
						amp=5.0
						scanState = 1
							
					elif scanState == 1: #read counts at high amplitude all channels should report max counts
						#----------------------------------------
						for feb in self.Febs:
							aAsics = self.Febs[feb].activeAsics
							if (febCounts[feb][ch]<int(meas_time*freq*0.95) and 0 in aAsics):
							#if febCounts[feb][ch]<int(meas_time*freq*0.95) or febCounts[feb][ch+8]<int(meas_time*freq*0.95): 
								self.Febs[feb].FEBok = False
								self.Febs[feb].log("Channel: %d gives unexpected response!"%(ch),"red",1)
								status = False
							if (febCounts[feb][ch+8]<int(meas_time*freq*0.95) and 1 in aAsics):
							#if febCounts[feb][ch]<int(meas_time*freq*0.95) or febCounts[feb][ch+8]<int(meas_time*freq*0.95): 
								self.Febs[feb].FEBok = False
								self.Febs[feb].log("Channel: %d gives unexpected response!"%(ch+8),"red",1)
								status = False
							if febCounts[feb][ch]<int(meas_time*freq*0.95): self.Febs[feb].measData["FebInfo"]["QuickChannelsTestStatus"][ch] = 0
							if febCounts[feb][ch+8]<int(meas_time*freq*0.95): self.Febs[feb].measData["FebInfo"]["QuickChannelsTestStatus"][ch+8] = 0
						break
					
		
		self.gen.set_output_state((1,2),False)
		self.Injectors.setActiveChannel(None)
		etime = datetime.datetime.now() 
		printc("Quick channels test for FEBs: %s took: %s"%(str(list(self.Febs.keys())),str(etime-stime).split(".")[0]),"blue",0)
		for feb in self.Febs: self.Febs[feb].log("Quick channels test took: %s"%(str(etime-stime).split(".")[0]),"blue",0,False)
		return status



	#Function run scurve scan measurement for all FEB's given as class argument
	########################################################################################################
	def runScurveScan(self,measName,injChns=None):
		stime = datetime.datetime.now() 
		printc("Scurve Scan for FEBs: %s started at: %s"%(str(list(self.Febs.keys())),stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0)
		measKey=self.measSCurveID+measName
		meas_time=0.5
		freq = 600.0e3
		stepH=0.1
		stepL=0.01
		
		if injChns == None: injChns = list(range(8))
		
		#initialize output data dictionaries in FEbs
		for feb in self.Febs: 
			self.Febs[feb].log("Scurve Scan started at: %s"%(stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0,False)
			info = self.Febs[feb].getFullConfiguration()
			info["date"] = stime.strftime("%d.%m.%Y %H:%M:%S")
			self.Febs[feb].measData[measKey] = {"info":info}
			for ch in injChns:
				self.Febs[feb].measData[measKey][ch]={"A":[],"C":[],"convFactor": self.Febs[feb].convFactors[ch]}
				self.Febs[feb].measData[measKey][ch+8]={"A":[],"C":[],"convFactor": self.Febs[feb].convFactors[ch+8]}
		
		#Setting starting amplitude based on the vth setting from last measured feb
		StartAmp = round(float(info["vth"])*0.03/0.05,0)*0.05  #rounded to 0.05
		if StartAmp < 0.05: StartAmp = 0.05
		
		for ch in injChns:
				self.Injectors.setActiveChannel(ch)
				printc("Charge injected to channels: %d and %d"%(ch,ch+8),"purple",0)
				for feb in self.Febs: self.Febs[feb].log("Charge injected to channels: %d and %d"%(ch,ch+8),"purple",0,False)
				amp = StartAmp  #starting amplitude
				magicAmp=0.0
				self.gen.set_frequency((1,2),freq)
				self.gen.set_amplitude((1,2),amp)
				self.gen.set_output_state((1,2),True)
				
				scanState=0
				extraSteps=6
				ampDelay=0.5
				
				while(1):
					self.gen.set_amplitude((1,2),amp)
					time.sleep(ampDelay)
					febCounts = self.DataReader.getCounts(meas_time)
					
					txt="A: %0.3f[V] %d %0.1f  "%(round(amp,3),extraSteps,ampDelay)
					for feb in self.Febs: 
						txt+="%d:[%6d,%6d] "%(feb,febCounts[feb][ch],febCounts[feb][ch+8])
						self.Febs[feb].log("A: %0.3f[V] [%6d,%6d]  [counts]"%(round(amp,3),febCounts[feb][ch],febCounts[feb][ch+8]),"green",1,False)
					printc(txt+" [counts]","green",1)
					
					if scanState == 0: #search for magicAmp where all channel gives more than 10-12k counts
						#----------------------------------------
						if self.countsIsOverTh(febCounts,ch,int(meas_time*freq*0.04)): #%stop when counts are over 4% of max 
							magicAmp=amp
							scanState = 1
						else:
							amp+=stepH
							ampDelay=0.05
							if amp > 5.0: 
								self.gen.set_output_state((1,2),False)
								self.Injectors.setActiveChannel(None)
								return False
							
					elif scanState == 1: #data collecting from magicAmp down to minimum
						#----------------------------------------
						#print(febCounts[0],extraSteps,round(amp,3),scanState)
						ampDelay=0.15
						for feb in self.Febs:
							self.Febs[feb].measData[measKey][ch]["A"].insert(0,round(amp,3))
							self.Febs[feb].measData[measKey][ch]["C"].insert(0,febCounts[feb][ch])
							self.Febs[feb].measData[measKey][ch+8]["A"].insert(0,round(amp,3))
							self.Febs[feb].measData[measKey][ch+8]["C"].insert(0,febCounts[feb][ch+8])
						if self.countsIsBelowTh(febCounts,ch,int(meas_time*freq*0.02)): #%stop when counts are below 2% of max 
							extraSteps-=1
						amp-=stepL*(7-extraSteps) #Extra steps when counts is saturated
						if extraSteps == 0 or amp < 0.05:
							amp = magicAmp + stepL
							scanState = 2
							extraSteps = 6
							ampDelay=0.5
							
					elif scanState == 2: #data collecting from magicAmp to maximum
						#----------------------------------------
						#print(febCounts[0],extraSteps,round(amp,3),scanState)
						ampDelay=0.15
						for feb in self.Febs:
							self.Febs[feb].measData[measKey][ch]["A"].append(round(amp,3))
							self.Febs[feb].measData[measKey][ch]["C"].append(febCounts[feb][ch])
							self.Febs[feb].measData[measKey][ch+8]["A"].append(round(amp,3))
							self.Febs[feb].measData[measKey][ch+8]["C"].append(febCounts[feb][ch+8])
						if self.countsIsOverTh(febCounts,ch,int(meas_time*freq)): 
							extraSteps-=1 
						amp+=stepL*(7-extraSteps)  #Extra steps when counts is saturated
						if extraSteps == 0 or amp > 5.0:
							break
		
		self.gen.set_output_state((1,2),False)
		self.Injectors.setActiveChannel(None)
		etime = datetime.datetime.now() 
		printc("Scurve Scan for FEBs: %s took: %s"%(str(list(self.Febs.keys())),str(etime-stime).split(".")[0]),"blue",0)
		for feb in self.Febs: self.Febs[feb].log("Scurve Scan took: %s"%(str(etime-stime).split(".")[0]),"blue",0,False)
		return True




	#Function run scurve scan measurement for one FEB (branch)
	#This is callibration scan. Data are collected only from channel 0 of the FEB, which must be connected to selected injector channel
	#Chn should be in range 0-15 - channel currently connected to channel 0 on FEB test board
	########################################################################################################
	def runScurveCalibrationScan(self,measName,feb,Chn):
		stime = datetime.datetime.now() 
		printc("Scurve Calibration Scan for FEB: %d and Injector channel: %d started at: %s"%(feb,Chn,stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0)
		measKey=self.measSCurveID+measName
		meas_time=0.5
		freq = 600.0e3
		stepH=0.1
		stepL=0.005
		
		#initialize output data dictionaries in FEbs
		self.Febs[feb].log("Scurve Calibration Scan started at: %s"%(stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0,False)
		info = self.Febs[feb].getFullConfiguration()
		info["date"] = stime.strftime("%d.%m.%Y %H:%M:%S")
		self.Febs[feb].measData[measKey] = {"info":info}
		self.Febs[feb].measData[measKey][Chn]={"A":[],"C":[],"convFactor": self.Febs[feb].convFactors[Chn]}


		self.Injectors.setActiveChannel(Chn%8)
		printc("Charge injected to channel: %d"%(Chn),"purple",0)
		self.Febs[feb].log("Charge injected to channel: %d"%(Chn),"purple",0,False)
		amp = 3.30  #starting amplitude
		magicAmp=0.0
		self.gen.set_frequency((1,2),freq)
		self.gen.set_amplitude((1,2),amp)
		self.gen.set_output_state((1,2),True)
		
		scanState=0
		extraSteps=6
		ampDelay=0.5
		
		while(1):
			self.gen.set_amplitude((1,2),amp)
			time.sleep(ampDelay)
			febCounts = self.DataReader.getCounts(meas_time)
			
			txt="A: %0.3f[V] %d %0.1f  "%(round(amp,3),extraSteps,ampDelay)
			txt+="%d:[%6d] "%(feb,febCounts[feb][0])
			self.Febs[feb].log("A: %0.3f[V] [%6d]  [counts]"%(round(amp,3),febCounts[feb][0]),"green",1,False)
			printc(txt+" [counts]","green",1)
			
			if scanState == 0: #search for magicAmp where all channel gives more than 10-12k counts
				#----------------------------------------
				if febCounts[feb][0]>=int(meas_time*freq*0.04): #%stop when counts are over 4% of max 
					magicAmp=amp
					scanState = 1
				else:
					amp+=stepH
					ampDelay=0.05
					if amp > 5.0: 
						self.gen.set_output_state((1,2),False)
						self.Injectors.setActiveChannel(None)
						return False
					
			elif scanState == 1: #data collecting from magicAmp down to minimum
				#----------------------------------------
				#print(febCounts[0],extraSteps,round(amp,3),scanState)
				ampDelay=0.15
				self.Febs[feb].measData[measKey][Chn]["A"].insert(0,round(amp,3))
				self.Febs[feb].measData[measKey][Chn]["C"].insert(0,febCounts[feb][0])
				if febCounts[feb][0]<int(meas_time*freq*0.02): #%stop when counts are below 2% of max 
					extraSteps-=1
				amp-=stepL*(7-extraSteps) #Extra steps when counts is saturated
				if extraSteps == 0 or amp < 0.05:
					amp = magicAmp + stepL
					scanState = 2
					extraSteps = 6
					ampDelay=0.5
					
			elif scanState == 2: #data collecting from magicAmp to maximum
				#----------------------------------------
				#print(febCounts[0],extraSteps,round(amp,3),scanState)
				ampDelay=0.15
				self.Febs[feb].measData[measKey][Chn]["A"].append(round(amp,3))
				self.Febs[feb].measData[measKey][Chn]["C"].append(febCounts[feb][0])
				if febCounts[feb][0]>=int(meas_time*freq): 
					extraSteps-=1 
				amp+=stepL*(7-extraSteps)  #Extra steps when counts is saturated
				if extraSteps == 0 or amp > 5.0:
					break
		
		self.gen.set_output_state((1,2),False)
		self.Injectors.setActiveChannel(None)
		etime = datetime.datetime.now() 
		printc("Scurve Calibration Scan for FEB: %d took: %s"%(feb,str(etime-stime).split(".")[0]),"blue",0)
		self.Febs[feb].log("Scurve Scan took: %s"%(str(etime-stime).split(".")[0]),"blue",0,False)
		return True


	#-------------------------------------
	#        Fitting and calculations Functions
	#--------------------------------------
	
	#Function to fit to s-curve
	########################################################################################################
	def f_erf(self,x,p0,p1,p2,p3):
		return p0*spec.erf(p2*(x-p1))+p3
	
	
	#Function fits error function to all channels . 
	#Calculated parameters are stored in fittedData dictionary in FEB
	########################################################################################################
	def fitScurveData(self,measName=None):
		retval = True
		selectedMeas = self.selectedMeasurements(self.measSCurveID,measName)
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Fitting s-curve to: %s"%(measKey.replace(self.measSCurveID,"")),"blue",0)
				#fittedData[measSCurveID+measName][ch:{sigma:val, median: val, ...},ch:{sigma:val, median: val, ...}]
				self.Febs[feb].fittedData[measKey]={}
				inputData = self.Febs[feb].measData[measKey]
				#aAsics = self.Febs[feb].activeAsics #active channels, it will be limited if one of the asic doesn't answer
				#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16))
				activeChns = self.Febs[feb].activeChannels
				for ch in inputData:
					if ch == "info": continue
					if not ch in activeChns: continue
					Amp = inputData[ch]["A"]
					Counts = inputData[ch]["C"]
					convFactor = inputData[ch]["convFactor"]
					try:
						normCounts = array([float(cnt) / max(Counts) for cnt in Counts])
						Qin = array([float(a) * convFactor for a in Amp])
						
						# Fitting line to get sigma and median test values, to initial parameters of scurve fit
						sel_slope = abs(normCounts - 0.5) < 0.4       
						
						slope, intercept, r_value, p_value, std_err = stats.linregress(Qin[sel_slope], normCounts[sel_slope])
						medianInit = (0.5 - intercept)/slope
						x1 = (0.16 - intercept)/slope
						x2 = (0.84 - intercept)/slope
						sigmaFWHM = (x2-x1)/2  #Calculated as half value of FWHM
						
						# Fitting s-curve function
						param_init = [0.5, medianInit, 1/(sqrt(2)*sigmaFWHM),  0.5]
						param, pcov = opt.curve_fit(self.f_erf,Qin,normCounts,param_init)
						#perr = sqrt(diag(pcov))
						self.Febs[feb].fittedData[measKey][ch]={"sigma":float(1.0/(param[2]*sqrt(2))), "sigmaFWHM":float(sigmaFWHM), "median":float(param[1]), "erfAmp":float(param[0]), "erfOffset":float(param[3])}
					
					except:
						e = sys.exc_info()[0]
						self.Febs[feb].fittedData[measKey][ch]={"sigma":0.0, "sigmaFWHM":0.0, "median":0.0, "erfAmp":0.0, "erfOffset":0.0}
						self.Febs[feb].log("fitScurveData error: %s"%(e.__name__),"red",0)
						retval = False
						
		return retval



	#Function calculate Gain and baseline based on Many Scurve measurements
	#measName parameter is used to select class of the S-curves with one parameter
	#dataName sets data name in FittedData dictionary in FEB class
	########################################################################################################
	def fitGainData(self,measName, dataName):
		retval = True
		dataKey = self.measSCurveID+dataName
		selectedMeas = self.selectedMeasurements(self.measSCurveID,measName)
		for feb in self.Febs:
			self.Febs[feb].log("Fitting Gain Curves to: %s"%((", ".join(selectedMeas[feb])).replace(self.measSCurveID,"")),"blue",0)
			self.Febs[feb].fittedData[dataKey]={}
			#aAsics = self.Febs[feb].activeAsics #active channels, it will be limited if one of the asic doesn't answer
			#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16)) 
			activeChns = self.Febs[feb].activeChannels
			#Preparing data series based on many S-Curve measurements ...
			for measKey in sorted(selectedMeas[feb]):
				Vth = self.Febs[feb].measData[measKey]["info"]["vth"]
				fittedData = self.Febs[feb].fittedData[measKey]
				for ch in range(16):
					if not ch in fittedData.keys(): continue
					if not ch in activeChns: continue
					if not ch in self.Febs[feb].fittedData[dataKey]: 
						self.Febs[feb].fittedData[dataKey][ch]={"T":[],"M":[]}
					self.Febs[feb].fittedData[dataKey][ch]["T"].append(Vth)
					self.Febs[feb].fittedData[dataKey][ch]["M"].append(fittedData[ch]["median"])
			#Fitting data...
			vthOffsets=[0]*16
			for ch in self.Febs[feb].fittedData[dataKey]:
				Median = self.Febs[feb].fittedData[dataKey][ch]["M"] #x-axis
				Vth = self.Febs[feb].fittedData[dataKey][ch]["T"] #y-axis
				#for deriv calculations
				ArMedian = array([float(m) for m in Median])
				ArMedianderiv = ArMedian[1:] - ArMedian[:-1] #Calculate simple derivative (next - previous value)
				#print(ch,Median,"\n",Vth,"\n------------\n")
				#print(around(ArMedianderiv, decimals=4).tolist())
				self.Febs[feb].fittedData[dataKey][ch]["Mdnl"]=around(ArMedianderiv, decimals=4).tolist()
				try:
					#optimization may be added here
					gain, vthOffset, r_value, p_value, std_err = stats.linregress(Median, Vth)
					#print(gain, vthOffset, r_value, p_value, std_err)
					vthOffsets[ch] = float(vthOffset)
					self.Febs[feb].fittedData[dataKey][ch]["gain"] = float(gain)
					self.Febs[feb].fittedData[dataKey][ch]["vthOffset"] = float(vthOffset)
				except:
					e = sys.exc_info()[0]
					self.Febs[feb].fittedData[dataKey][ch]["gain"] = 0.0
					self.Febs[feb].fittedData[dataKey][ch]["vthOffset"] = 0.0
					self.Febs[feb].log("fitGainData error: %s"%e.__name__,"red",0)
					retval = False
			#Calculating Vth Errors
			for ch in self.Febs[feb].fittedData[dataKey]:
				self.Febs[feb].fittedData[dataKey][ch]["vthError"] = float(vthOffsets[ch] - mean(vthOffsets))
		return retval

		#
	
	
	#-------------------------------------
	#        Ploting Functions for one FEB
	#--------------------------------------

	#Function plot s-curve measurements data with fitted s-curves for all channels
	#Fitted parameters for all channels are shown on plots
	########################################################################################################
	def plotScurveDetails(self,measName=None):
		selectedMeas = self.selectedMeasurements(self.measSCurveID,measName)
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Plotting s-curve details: %s"%(measKey.replace(self.measSCurveID,"")),"blue",0)
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measSCurveID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				inputData = self.Febs[feb].measData[measKey]
			
				cm=1.0/2.54
				fig0,axsA0 = plt.subplots(4,2,figsize=(20*cm,30*cm))
				fig1,axsA1 = plt.subplots(4,2,figsize=(20*cm,30*cm))
				#fig0.tight_layout(pad=1.0)
				#fig1.tight_layout(pad=1.0)
				#fig0.subplots_adjust(hspace=0.3)
				
				for ch in fittedData:
					erf = fittedData[ch]
					
					#Getting input data for plot
					Amp = inputData[ch]["A"]
					Counts = inputData[ch]["C"]
					convFactor = inputData[ch]["convFactor"]
					
					#Creating x,y and erf data series for plot
					Qin = array([float(a) * convFactor for a in Amp])
					normCounts = array([float(cnt) / max(Counts) for cnt in Counts])
					QinErf = linspace(min(Qin),max(Qin),200) #x axis for fitted curve plotting
					fittedErf = erf["erfAmp"] * spec.erf( (QinErf-erf["median"])/(erf["sigma"]*sqrt(2)) ) + erf["erfOffset"]
					
					if ch<8: axs = axsA0[int(ch/2),int(ch%2)]
					else: axs = axsA1[int((ch-8)/2),int((ch-8)%2)]
						
					axs.plot(Qin,normCounts,"ko", label="Channel %02d"%(ch))
					axs.plot(QinErf,fittedErf,"r-", label="Fitted s-curve")
					axs.legend(ncol=1,loc="center left")
					axs.grid()
					
					txt="$\sigma_{FWHM} = %.2f$ $ke^-$\n$\sigma_{fit} = %.2f$ $ke^-$\n$median = %.2f$ $ke^-$"%(erf["sigmaFWHM"],erf["sigma"],erf["median"])
					axs.text(0.02, 0.97, txt, verticalalignment='top', horizontalalignment='left', 
													transform=axs.transAxes, bbox={'facecolor': 'green', 'alpha': 0.5, 'pad': 3}) #color='green',fontsize=15
					
					#axs.set_xlim(250,400)
					axs.set_xlabel("Input charge [$ke^-$]")
					axs.set_ylabel("Normalized counts [-]")
				
				#outFile = "%s_%s_%s"%(self.Febs[feb].userID,measKey,"details.png") 
				#plt.savefig(os.path.join(self.outDir,outFile),bbox_inches='tight', pad_inches=0.5) 
				
				outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
				outFile = "%s_%s_%s_%s.pdf"%(self.Febs[feb].userID,measKey.split("_")[0],"Details",measKey.split("_")[1]) 
				with PdfPages(os.path.join(outDir,outFile)) as pdf:
					pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
					pdf.savefig(fig1, bbox_inches='tight', pad_inches=0.2*cm)
				plt.close(fig0)
				plt.close(fig1)
	
	
	
	#Function plots s-curve parameters versus channels
	########################################################################################################
	def plotScurveParams(self,measName=None,extOutName=""):
		selectedMeas = self.selectedMeasurements(self.measSCurveID,measName)
		if extOutName != "": extOutName = "_" + extOutName
		for feb in self.Febs:
			cm=1.0/2.54
			fig0,axs = plt.subplots(1,2,figsize=(20*cm,10*cm))
			
			axsLim={0:[],1:[]}
			self.Febs[feb].log("Plotting s-curve parameters: %s"%((", ".join(selectedMeas[feb])).replace(self.measSCurveID,"")),"blue",0)
			if len(selectedMeas[feb])==0: continue
		
			#aAsics = self.Febs[feb].activeAsics #active channels, it will be limited if one of the asic doesn't answer
			#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16)) 
			activeChns = self.Febs[feb].activeChannels
			for measKey in selectedMeas[feb]:
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measSCurveID,""),self.Febs[feb].userID),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				#inputData = self.Febs[feb].measData[measKey]
			
				Channels = array([ch for ch in sorted(fittedData.keys())])
				Sigmas = array([fittedData[ch]["sigma"] for ch in sorted(fittedData.keys())])
				Medians = array([fittedData[ch]["median"] for ch in sorted(fittedData.keys())])
				#limit values for plot yrange customization
				axsLim[0]+=[max(Sigmas),min(Sigmas)]
				axsLim[1]+=[max(Medians),min(Medians)]
				
				axs[0].plot(Channels,Sigmas,"o:",linewidth=0.5, label=measKey.replace(self.measSCurveID,""))
				axs[1].plot(Channels,Medians,"o:",linewidth=0.5, label=measKey.replace(self.measSCurveID,""))

			axs[0].legend(ncol=3,loc="upper center", fontsize='x-small')
			axs[0].grid()
			axs[0].set_ylim(min(axsLim[0])-0.25,max(axsLim[0])+0.25)
			axs[0].set_xlabel("Channel number [-]")
			axs[0].set_ylabel("Sigma [$ke^-$]")
			axs[0].set_xticks([2*t for t in range(8)])
			axs[0].set_xlim(min(Channels)-0.5,max(Channels)+0.5)
			
			axs[1].legend(ncol=3,loc="upper center", fontsize='x-small')
			axs[1].grid()
			axs[1].set_ylim(min(axsLim[1])*0.85,max(axsLim[1])*1.15)
			axs[1].set_xlabel("Channel number [-]")
			axs[1].set_ylabel("Median [$ke^-$]")
			axs[1].set_xticks([2*t for t in range(8)])
			axs[1].set_xlim(min(Channels)-0.5,max(Channels)+0.5)
			
			#outFile = "%s_%s_%s"%(self.Febs[feb].userID,measKey,"params.png") 
			#plt.savefig(os.path.join(self.outDir,outFile),bbox_inches='tight') 
				
			outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
			outFile = "%s_%s.pdf"%(self.Febs[feb].userID,self.measSCurveID+"Params"+extOutName) 
			axs[1].text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs[1].transAxes, rotation=90, fontsize=6,alpha=0.4)
			
			with PdfPages(os.path.join(outDir,outFile)) as pdf:
				pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
			plt.close(fig0)
	
	
	
	########################################################################################################
	def plotFittedCurves(self,measName=None):
		selectedMeas = self.selectedMeasurements(self.measSCurveID,measName)
		for feb in self.Febs:
			self.Febs[feb].log("Plotting s-curves: %s"%((", ".join(selectedMeas[feb])).replace(self.measSCurveID,"")),"blue",0)
			for measKey in selectedMeas[feb]:
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measSCurveID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				inputData = self.Febs[feb].measData[measKey]
			
				cm=1.0/2.54
				fig0,axs = plt.subplots(1,1,figsize=(20*cm,7.5*cm))
				
				medians=[]
				sigmas=[]
				for ch in sorted(fittedData.keys()):
					erf = fittedData[ch]
					medians.append(erf["median"])
					sigmas.append(erf["sigma"])
					
					#Getting input data for plot
					Amp = inputData[ch]["A"]
					convFactor = inputData[ch]["convFactor"]
					
					QinErf = linspace(min(Amp)*convFactor,max(Amp)*convFactor,200) #x axis for fitted curve plotting
					fittedErf = erf["erfAmp"] * spec.erf( (QinErf-erf["median"])/(erf["sigma"]*sqrt(2)) ) + erf["erfOffset"]

					axs.plot(QinErf,fittedErf,"-", label="Channel %02d"%(ch))
				
				#axs.legend(ncol=8, loc="upper center", bbox_to_anchor=(0.5, 1.12), fontsize='xx-small')
				axs.legend(ncol=1, loc="center right", fontsize='x-small')
				axs.grid()
					
				txt="$Max = %.2f$ $ke^-$\n$Min = %.2f$ $ke^-$\n$\Delta = %.2f$ $ke^-$\n$\Delta = %.2f$ $fC$"%(max(medians),min(medians),max(medians)-min(medians),(max(medians)-min(medians)) * echarge * 1000 * 10**15)
				axs.text(0.02, 0.97, txt, verticalalignment='top', horizontalalignment='left', 
												transform=axs.transAxes, bbox={'facecolor': 'green', 'alpha': 0.5, 'pad': 3}) #color='green',fontsize=15
				
				axs.set_xlim(average(medians)-10*max(sigmas),average(medians)+10*max(sigmas))
				axs.set_xlabel("Input charge [$ke^-$]")
				axs.set_ylabel("Normalized counts [-]")
				
				#outFile = "%s_%s_%s"%(self.Febs[feb].userID,measKey,"details.png") 
				#plt.savefig(os.path.join(self.outDir,outFile),bbox_inches='tight', pad_inches=0.5) 
				
				outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
				outFile = "%s_%s_%s_%s.pdf"%(self.Febs[feb].userID,measKey.split("_")[0],"ScurvesComp",measKey.split("_")[1]) 
				axs.text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs.transAxes, rotation=90, fontsize=6,alpha=0.4)
			
				with PdfPages(os.path.join(outDir,outFile)) as pdf:
					pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
				plt.close(fig0)



	#Function plots gain curves (S-Curve median vs Threshold) based on many S-Curve measurements fitted before
	########################################################################################################
	def plotGainCurves(self,dataName):
		dataKey = self.measSCurveID+dataName
		for feb in self.Febs:
			self.Febs[feb].log("Plotting gain curves: %s"%(dataName),"blue",0)
			if not dataKey in self.Febs[feb].fittedData.keys(): continue
			fittedData = self.Febs[feb].fittedData[dataKey]
			cm=1.0/2.54
			fig0,axs = plt.subplots(1,1,figsize=(20*cm,13*cm))
			
			#ploting data and fitted lines...
			for ch in sorted(fittedData.keys()):
				Median = fittedData[ch]["M"]
				Vth = fittedData[ch]["T"]
				axs.plot(Median,Vth,"o", label="Channel %02d"%(ch))
				
			axs.set_prop_cycle(plotCycler)
			txt = "Gains: [LSB/$ke^-$],   [mV/fC]*:\n\n"
			#txt=""
			for ch in sorted(fittedData.keys()):
				ArMedian = array([float(m) for m in fittedData[ch]["M"]])
				ArLine = fittedData[ch]["gain"] * ArMedian + fittedData[ch]["vthOffset"]
				axs.plot(ArMedian,ArLine,"-")
				txt+="%02d:  %0.5f,   %0.3f\n"%(ch,fittedData[ch]["gain"],fittedData[ch]["gain"]*12.48299) #lsb/ke- -> mV/fC
			
			txt+="\n*LSB = 2mV was assumed"
			axs.text(0.04, 0.95, txt, verticalalignment='top', horizontalalignment='left', 
													transform=axs.transAxes, bbox={'facecolor': 'blue', 'alpha': 0.3, 'pad': 3},fontsize=7) 
			
			axs.legend(ncol=1, loc="center right", fontsize='x-small')
			
			axs.grid()
			axs.set_xlabel("Median [$ke^-$]")
			axs.set_ylabel("Threshold Setting [LSB]")

			outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
			outFile = "%s_%s%s_%s.pdf"%(self.Febs[feb].userID,self.measSCurveID,"ChannelGains",dataName) 
			axs.text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs.transAxes, rotation=90, fontsize=6,alpha=0.4)
			
			with PdfPages(os.path.join(outDir,outFile)) as pdf:
				pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
			plt.close(fig0)

	
	
	#Function plots gain parameters based on many S-Curve measurements fitted before
	########################################################################################################
	def plotGainParams(self,dataNames):
		for feb in self.Febs:
			cm=1.0/2.54
			fig0,axs = plt.subplots(2,1,figsize=(20*cm,18*cm))
			axsLim={0:[],1:[]}
			self.Febs[feb].log("Plotting gain parameters: %s"%(", ".join(dataNames)),"blue",0)
			missingData=True
			for dataName in dataNames:
				dataKey = self.measSCurveID+dataName
				if not dataKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(dataName),"orange",0)
					continue
				missingData=False
				fittedData = self.Febs[feb].fittedData[dataKey]
				Channels = array([ch for ch in sorted(fittedData.keys())])
				Gains = array([fittedData[ch]["gain"]*12.48299 for ch in sorted(fittedData.keys())])
				Offset = array([fittedData[ch]["vthOffset"] for ch in sorted(fittedData.keys())])
				#OffsetErr = array([fittedData[ch]["vthError"] for ch in sorted(fittedData.keys())])
				
				#limit values for plot yrange customization
				axsLim[0]+=[max(Gains),min(Gains)]
				axsLim[1]+=[max(Offset),min(Offset)]
				#axsLim[1]+=[max(OffsetErr),min(OffsetErr)]
				
				axs[0].plot(Channels,Gains,"o:",linewidth=0.5, label=dataName.replace("Gain",""))
				axs[1].plot(Channels,Offset,"o:",linewidth=0.5, label=dataName.replace("Gain",""))
				#axs[1].plot(Channels,OffsetErr,"o:",linewidth=0.5, label=dataName.replace("Gain",""))
			
			if missingData: continue
			
			axs[0].legend(ncol=5,loc="upper center")
			axs[0].grid()
			axs[0].set_ylim(0.5,max(axsLim[0])+1.0)
			axs[0].set_xlabel("Channel number [-]")
			axs[0].set_ylabel("Gain [mV/fC]")
			
			axs[1].legend(ncol=5,loc="upper center")
			axs[1].grid()
			axs[1].set_ylim(min(axsLim[1])-0.2,max(axsLim[1])+0.4)
			axs[1].set_xlabel("Channel number [-]")
			axs[1].set_ylabel("Threshold Offset [LSB]")
			
			outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
			outFile = "%s_%s%s_%s.pdf"%(self.Febs[feb].userID,self.measSCurveID,"ChannelGains","Parameters") 
			axs[1].text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs[1].transAxes, rotation=90, fontsize=6,alpha=0.4)
			
			with PdfPages(os.path.join(outDir,outFile)) as pdf:
				pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
			plt.close(fig0)
	
	
	#Function plots median DNL (S-Curve median dnl vs Threshold) based on many S-Curve measurements fitted before
	########################################################################################################
	def plotMedianDnl(self,dataName):
		dataKey = self.measSCurveID+dataName
		for feb in self.Febs:
			self.Febs[feb].log("Plotting Median DNL curves: %s"%(dataName),"blue",0)
			if not dataKey in self.Febs[feb].fittedData.keys(): continue
			fittedData = self.Febs[feb].fittedData[dataKey]
			cm=1.0/2.54
			axsLim=[]
			fig0,axs = plt.subplots(1,1,figsize=(20*cm,11*cm))
			
			#ploting data and fitted lines...
			for ch in sorted(fittedData.keys()):
				#Median = fittedData[ch]["M"]
				MedianDnl = fittedData[ch]["Mdnl"] #y
				Vth = fittedData[ch]["T"][:len(MedianDnl)] #x
				#axs.plot(Vth,MedianDnl,"o", label="Channel %02d"%(ch))
				axs.step(Vth,MedianDnl,where='post', label="Channel %02d"%(ch))
				
				axsLim+=[max(MedianDnl),min(MedianDnl)]
				
			#axs.legend(ncol=1, loc="center right", fontsize='x-small')
			axs.legend(ncol=4,loc="lower center", fontsize='x-small')
			
			axs.grid()
			axs.set_ylim(0.0,max(axsLim)+0.5)
			axs.set_xlabel("Threshold Setting [LSB]")
			axs.set_ylabel("Median DNL [$ke^-$]")
			
			outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
			outFile = "%s_%s%s_%s.pdf"%(self.Febs[feb].userID,self.measSCurveID,"MedianDNL",dataName) 
			axs.text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs.transAxes, rotation=90, fontsize=6,alpha=0.4)
			
			with PdfPages(os.path.join(outDir,outFile)) as pdf:
				pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
			plt.close(fig0)
	
	
	
	
	
	#-------------------------------------
	#        Ploting Functions - comparison for all Febs
	#--------------------------------------

	#Function plots s-curve parameters versus channels
	#All FEB's in one plot
	########################################################################################################
	def plotScurveParamsCompare(self,measName=None):
		selectedMeas = self.selectedMeasurements(self.measSCurveID,measName)
		selectedMeasFlat=[]
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				if not measKey in selectedMeasFlat: selectedMeasFlat.append(measKey)
		for measKey in selectedMeasFlat:
			printc("Plotting s-curve comparison for measurement: %s"%(measKey.replace(self.measSCurveID,"")),"blue",0)
			cm=1.0/2.54
			fig0,axs = plt.subplots(2,1,figsize=(20*cm,15*cm))
			
			axsLim={0:[],1:[]}
			for feb in self.Febs:
				self.Febs[feb].log("Plotting s-curve comparison for measurement: %s"%(measKey.replace(self.measSCurveID,"")),"blue",0, False)
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measSCurveID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				#inputData = self.Febs[feb].measData[measKey]
			
				Channels = array([ch for ch in sorted(fittedData.keys())])
				Sigmas = array([fittedData[ch]["sigma"] for ch in sorted(fittedData.keys())])
				Medians = array([fittedData[ch]["median"] for ch in sorted(fittedData.keys())])
				#limit values for plot yrange customization
				axsLim[0]+=[max(Sigmas),min(Sigmas)]
				axsLim[1]+=[max(Medians),min(Medians)]
				
				axs[0].plot(Channels,Sigmas,"o:",linewidth=0.5, label=self.Febs[feb].userID)
				axs[1].plot(Channels,Medians,"o:",linewidth=0.5, label=self.Febs[feb].userID)

			axs[0].legend(ncol=8,loc="upper center", fontsize='x-small')
			axs[0].grid()
			axs[0].set_ylim(min(axsLim[0])-0.1,max(axsLim[0])+0.1)
			axs[0].set_xlabel("Channel number [-]")
			axs[0].set_ylabel("Sigma [$ke^-$]")
			
			axs[1].legend(ncol=8,loc="upper center", fontsize='x-small')
			axs[1].grid()
			axs[1].set_ylim(min(axsLim[1])*0.95,max(axsLim[1])*1.05)
			axs[1].set_xlabel("Channel number [-]")
			axs[1].set_ylabel("Median [$ke^-$]")
			
			outDir = os.path.join(ReportsPath)
			outFile = "%s_%s_%s_%s.pdf"%("FEBsCompare",measKey.split("_")[0],"Params",measKey.split("_")[1]) 
			axs[1].text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs[1].transAxes, rotation=90, fontsize=6,alpha=0.4)
			
			with PdfPages(os.path.join(outDir,outFile)) as pdf:
				pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
			plt.close(fig0)



#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------


if __name__=="__main__":
	
	from PANDAfeb import PANDAfeb
	Feb = PANDAfeb(0,"B000",True) #creating object as data reader only
	Feb2 = PANDAfeb(0,"B001",True) #creating object as data reader only
	
	Febs={0:Feb}#,1:Feb2}
	
	sCurveMeas = measSCurve(None,None,None,Febs)
	#sCurveMeas.fitScurveData()

	#sCurveMeas.plotScurveDetails()
	#sCurveMeas.plotScurveParams("Th015","Th015") #"4mV15nsTh0(0[6-9]|1[0-3])"
	#sCurveMeas.plotFittedCurves()
	#sCurveMeas.plotScurveParamsCompare()
	
	
	sCurveMeas.fitGainData("1mV20nsTh0[0-2]","1mV20nsGain")
	sCurveMeas.fitGainData("2mV15nsTh0[0-2]","2mV15nsGain")
	sCurveMeas.fitGainData("2mV20nsTh0[0-2]","2mV20nsGain")
	sCurveMeas.fitGainData("4mV15nsTh0[0-2]","4mV15nsGain")
	sCurveMeas.fitGainData("4mV20nsTh0[0-2]","4mV20nsGain")
	
	#print(Febs[0].fittedData["SCurve_4mV20nsGain"])
	
	
	sCurveMeas.plotGainCurves("1mV20nsGain")
	sCurveMeas.plotGainCurves("4mV20nsGain")

	sCurveMeas.plotGainParams(["1mV20nsGain","2mV15nsGain","2mV20nsGain","4mV15nsGain","4mV20nsGain"])
	#sCurveMeas.plotScurveParams(["test1","test2"],"testy12")
	#sCurveMeas.plotScurveParams(["test3"],"tylkoTest3")


