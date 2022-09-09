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
class measBaseline():
	#set font size of plot
	plt.rc('lines', linewidth=1, markersize=2)
	plt.rc('font', size=8)
	plt.rc('axes', prop_cycle=plotCycler)
	#MeasID will be added to Meas name for better measurements type recognizing
	measBaseID="Base_" 
	measBaseThID="BaseTh_" 
	
	#--------------- ----------------------
	#        INIT and general functions and private
	#--------------------------------------
	def __init__(self,gen,DataReader,Injectors,Febs):
		self.gen = gen
		self.DataReader = DataReader
		self.Injectors = Injectors
		self.Febs = Febs
	
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
				


	#Function converts fitted data from specify measBaseID measurement to list for baseline setting function in FEB
	#returns dictionary {feb1:[16*baseVal],feb2:[16*baseVal],...}
	#When optional argument Normalization is True, all baselines settings will be shifted to 
	#the highest posible values keeping baseline corrections
	########################################################################################################
	def getBaselineSettings(self, measName, Normalization="Center"):
		baselines={}
		for feb in self.Febs:
			basevals = [0]*16
			if not self.measBaseID+measName in self.Febs[feb].fittedData.keys(): continue
			#aAsics = self.Febs[feb].activeAsics
			#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16))
			activeChns = self.Febs[feb].activeChannels
			for ch in activeChns:
				basevals[ch] = self.Febs[feb].fittedData[self.measBaseID+measName][ch]["baseSetting"]
			if Normalization=="Center":
				baselines[feb]=basevals
			elif Normalization=="High":
				sh=31-max([basevals[ch] for ch in activeChns])
				for i in activeChns: basevals[i] = basevals[i] + sh
				baselines[feb]=basevals
			elif Normalization=="Low":
				sh=min([basevals[ch] for ch in activeChns])
				for i in activeChns: basevals[i] = basevals[i] - sh
				baselines[feb]=basevals
			else:
				baselines[feb]=[0]*16
		if not Normalization in ["Center","High","Low"]:
			self.Febs[feb].log("Unknown normalization: %s ! Default values was returned."%(Normalization),"orange",0)
		return baselines
				


	#--------------- ----------------------
	#        Measurements Functions
	#--------------------------------------
	
	
	#Function perform measuremnts of Baselines for all FEBs
	#measData are stored directly in FEBs dictionaries
	########################################################################################################
	def runBaselineSimple(self,measName): 
		stime = datetime.datetime.now() 
		printc("Baseline simple measurements for FEBs: %s started at: %s"%(str(list(self.Febs.keys())),stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0)
		measKey=self.measBaseID+measName
		meas_time=0.5
		
		#setting Th to 0 for all febs:
		printc("Setting threshold: %d"%(0),"purple",0)
		for feb in self.Febs:
			self.Febs[feb].setThreshold(0)
			
		#initialize output data dictionaries in FEbs
		for feb in self.Febs: 
			self.Febs[feb].log("Baseline simple measurements started at: %s"%(stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0,False)
			info = self.Febs[feb].getFullConfiguration()
			del info["base"]
			info["date"] = stime.strftime("%d.%m.%Y %H:%M:%S")
			self.Febs[feb].measData[measKey] = {"info":info}
			for ch in range(16):
				self.Febs[feb].measData[measKey][ch]={"B":[],"C":[]}
		
		amp = {0:0.22, 1:0.44, 2:0.88}[info["gain"]] #0.22 typical for gain 4 etc.
		#Setting some extra noise 
		self.gen.set_amplitude((1,2),amp)  
		self.gen.set_frequency((1,2),10.0e6) #10MHz, over FE bandwidth
		self.gen.set_output_state((1,2),True)
		
		#switch on all Injectors channels
		self.Injectors.setActiveChannelMask(255)
		
		for baseVal in range(32):
			printc("Setting baselines: %s"%(str([baseVal]*16)),"purple",0)
			for feb in self.Febs:
				self.Febs[feb].setBaselines([baseVal]*16)
			time.sleep(0.1)
			
			febCounts = self.DataReader.getCounts(meas_time)
					
			for feb in self.Febs:
				prtStr="["
				for ch in range(16):
					self.Febs[feb].measData[measKey][ch]["B"].append(baseVal)
					self.Febs[feb].measData[measKey][ch]["C"].append(febCounts[feb][ch])
					prtStr+="%7d,"%febCounts[feb][ch]
				self.Febs[feb].log("%s] [counts]"%(prtStr.rstrip(",")),"green",1)
				
		#disable all injector channels after mesurements 
		self.Injectors.setActiveChannel(None)
		self.gen.set_output_state((1,2),False)
		etime = datetime.datetime.now() 
		printc("Baseline simple measurements for FEBs: %s took: %s"%(str(list(self.Febs.keys())),str(etime-stime).split(".")[0]),"blue",0)
		for feb in self.Febs: self.Febs[feb].log("Baseline simple measurements took: %s"%(str(etime-stime).split(".")[0]),"blue",0,False)
		
		return True



	#Function perform threshold scan for all FEBs
	#measData are stored directly in FEBs dictionaries
	########################################################################################################
	def runThresholdScan(self,measName):   
		stime = datetime.datetime.now() 
		printc("Baseline threshold scan for FEBs: %s started at: %s"%(str(list(self.Febs.keys())),stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0)
		measKey=self.measBaseThID+measName
		meas_time=0.5
		
		#initialize output data dictionaries in FEbs
		for feb in self.Febs: 
			self.Febs[feb].log("Baseline threshold scan started at: %s"%(stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0,False)
			info = self.Febs[feb].getFullConfiguration()
			del info["vth"]
			info["date"] = stime.strftime("%d.%m.%Y %H:%M:%S")
			self.Febs[feb].measData[measKey] = {"info":info}
			for ch in range(16):
				self.Febs[feb].measData[measKey][ch]={"T":[],"C":[]}
		
		amp = {0:0.22, 1:0.44, 2:0.88}[info["gain"]] #0.22 typical for gain 4 etc.
		#Setting some extra noise 
		self.gen.set_amplitude((1,2),amp)
		self.gen.set_frequency((1,2),10.0e6) #10MHz, over FE bandwidth
		self.gen.set_output_state((1,2),True)
		
		#switch on all Injectors channels
		self.Injectors.setActiveChannelMask(255)
		
		#BreakEna = False
		
		for thVal in range(20):
			printc("Setting threshold: %d"%(thVal),"purple",0)
			for feb in self.Febs:
				self.Febs[feb].setThreshold(thVal)
			time.sleep(0.1)
			#reading counts...
			febCounts = self.DataReader.getCounts(meas_time)
			#SumCnts=0
			for feb in self.Febs:
				prtStr="["
				for ch in range(16):
					self.Febs[feb].measData[measKey][ch]["T"].append(thVal)
					self.Febs[feb].measData[measKey][ch]["C"].append(febCounts[feb][ch])
					#SumCnts+=febCounts[feb][ch]
					prtStr+="%7d,"%febCounts[feb][ch]
				self.Febs[feb].log("%s] [counts]"%(prtStr.rstrip(",")),"green",1)
			#End Scan conditions
			#if SumCnts > 0: BreakEna = True
			#if BreakEna and SumCnts==0: break
			
		#disable all injector channels after mesurements 
		self.Injectors.setActiveChannel(None)
		self.gen.set_output_state((1,2),False)
		etime = datetime.datetime.now() 
		printc("Baseline threshold scan for FEBs: %s took: %s"%(str(list(self.Febs.keys())),str(etime-stime).split(".")[0]),"blue",0)
		for feb in self.Febs: self.Febs[feb].log("Baseline threshold scan took: %s"%(str(etime-stime).split(".")[0]),"blue",0,False)
		
		return True


	#-------------------------------------
	#        Fitting and calculations Functions
	#--------------------------------------

	
	#Function calculate parameters from baseline measurements
	#Calculated parameters are stored in fittedData dictionary in FEB
	########################################################################################################
	def fitBaselineData(self,measName=None):
		retval = True
		selectedMeas = self.selectedMeasurements(self.measBaseID,measName)
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Calculating baselines from: %s"%(measKey.replace(self.measBaseID,"")),"blue",0)
				#fittedData[measBaseID+measName][ch:{baseVal:val, baseSetting: val, ...},ch:{baseVal:val, baseSetting: val, ...}]
				self.Febs[feb].fittedData[measKey]={}
				inputData = self.Febs[feb].measData[measKey]
				aAsics = self.Febs[feb].activeAsics #active channels, it will be limited if one of the asic doesn't answer
				#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16)) 
				activeChns = self.Febs[feb].activeChannels
				baseAV=0.0
				for ch in activeChns:
					BaseVal = inputData[ch]["B"]
					Counts = inputData[ch]["C"]
					Notes=[]
					try:
						ArBaseVal = array([float(b) for b in BaseVal])
						ArCounts = array([float(c) for c in Counts])
						
						base = 32 #value higher than max
						if sum(ArCounts) != 0:
							#Calculate average value of baseline
							base = sum(ArBaseVal*ArCounts)/sum(ArCounts)
						else:
							self.Febs[feb].log("Baseline at channel: %d too low, value 32 was assumed as raw baseline"%(ch),"red",1)
							Notes.append("Baseline at channel: %d too low, value 32 was assumed as raw baseline"%(ch))
							retval = False
							#self.Febs[feb].FEBok = False 
							
						baseAV += base/float(8.0*len(aAsics))
						self.Febs[feb].fittedData[measKey][ch]={"baseVal":float(base),"baseSetting":0, "baseAve":0.0, "baseNotes":Notes}
					except:
						e = sys.exc_info()[0]
						self.Febs[feb].fittedData[measKey][ch]={"baseVal":0.0,"baseSetting":0, "baseAve":0.0, "baseNotes":[]}
						self.Febs[feb].log("fitBaselineData error: %s"%e.__name__,"red",0)
						retval = False
				#calculating the best baseSetting and shift it to the center of the range
				for ch in activeChns:
					bset = self.Febs[feb].fittedData[measKey][ch]["baseVal"] - (baseAV-15.0)
					self.Febs[feb].fittedData[measKey][ch]["baseSetting"] = int(round(bset,0))
					self.Febs[feb].fittedData[measKey][ch]["baseAve"] = float(baseAV)
				
		return retval
		
		
		
	#Calculated parameters are stored in fittedData dictionary in FEB
	########################################################################################################
	def fitThresholdScanData(self,measName=None):
		retval = True
		selectedMeas = self.selectedMeasurements(self.measBaseThID,measName)
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Calculating thresholds from: %s"%(measKey.replace(self.measBaseThID,"")),"blue",0)
				#fittedData[measBaseThID+measName][ch:{baseVal:val, baseSetting: val, ...},ch:{baseVal:val, baseSetting: val, ...}]
				self.Febs[feb].fittedData[measKey]={}
				inputData = self.Febs[feb].measData[measKey]
				aAsics = self.Febs[feb].activeAsics #active channels, it will be limited if one of the asic doesn't answer
				#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16)) 
				activeChns = self.Febs[feb].activeChannels
				thAV=0.0
				for ch in activeChns:
					ThVal = inputData[ch]["T"]
					Counts = inputData[ch]["C"]
					Notes=[]
					try:
						ArThVal = array([float(b) for b in ThVal])
						ArCounts = array([float(c) for c in Counts])
						
						th = 0 #default value
						if sum(ArCounts) != 0:
							#Calculate average value of th
							th = sum(ArThVal*ArCounts)/sum(ArCounts)
						else:
							self.Febs[feb].log("Error during threshold calculation at channel: %d, deafault value 0 will be returned..."%(ch),"red",1)
							Notes.append("Error during threshold calculation at channel: %d, deafault value 0 will be returned..."%(ch))
							retval = False
							#self.Febs[feb].FEBok = False 

						thAV += th/float(8.0*len(aAsics))
						self.Febs[feb].fittedData[measKey][ch]={"thVal":float(th), "thAve":0.0, "thErr":0.0, "thNotes":Notes}
					except:
						e = sys.exc_info()[0]
						self.Febs[feb].fittedData[measKey][ch]={"thVal":0.0, "thAve":0.0, "thErr":0.0, "thNotes":[]}
						self.Febs[feb].log("fitThresholdScanData error: %s"%e.__name__,"red",0)
						retval = False
				for ch in activeChns:
					self.Febs[feb].fittedData[measKey][ch]["thAve"] = float(thAV)
					err = self.Febs[feb].fittedData[measKey][ch]["thVal"] - thAV
					self.Febs[feb].fittedData[measKey][ch]["thErr"] = float(err)

		return retval
	
	#-------------------------------------
	#        Ploting Functions
	#--------------------------------------


	#Fitted parameters for all channels are shown on plots
	########################################################################################################
	def plotBaselineDetails(self,measName=None):
		selectedMeas = self.selectedMeasurements(self.measBaseID,measName)
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Plotting baseline details: %s"%(measKey.replace(self.measBaseID,"")),"blue",0)
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measBaseID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				inputData = self.Febs[feb].measData[measKey]
				
				cm=1.0/2.54
				fig0,axsA0 = plt.subplots(4,2,figsize=(20*cm,30*cm))
				fig1,axsA1 = plt.subplots(4,2,figsize=(20*cm,30*cm))
				
				for ch in fittedData:
					fit = fittedData[ch]
					
					#Getting input data for plot
					BaseVal = inputData[ch]["B"]
					Counts = inputData[ch]["C"]
					
					if max(Counts) == 0: continue
					
					#Creating x  data series for plot
					normCounts = array([float(cnt) / max(Counts) for cnt in Counts])
					
					if ch<8: axs = axsA0[int(ch/2),int(ch%2)]
					else: axs = axsA1[int((ch-8)/2),int((ch-8)%2)]
						
					axs.plot(BaseVal,normCounts,"g-", label="Channel %02d"%(ch))
					axs.legend(ncol=1,loc="center left")
					axs.grid()
					
					txt="$B_{RAW} = %.2f$\n$B_{AVE} = %.2f$\n$B_{NORM} = %.2f$\n$B_{DAC} = %d$ ($B_{NORM}$+15)"%(fit["baseVal"], fit["baseAve"], fit["baseVal"]-fit["baseAve"],fit["baseSetting"])
					axs.text(0.02, 0.97, txt, verticalalignment='top', horizontalalignment='left', 
													transform=axs.transAxes, bbox={'facecolor': 'green', 'alpha': 0.5, 'pad': 3}) #color='green',fontsize=15
					
					#axs.set_xlim(250,400)
					axs.set_xlabel("Baseline Value [LSB]")
					axs.set_ylabel("Normalized counts [-]")
				
				outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
				outFile = "%s_%s_%s_%s.pdf"%(self.Febs[feb].userID,measKey.split("_")[0],"Details",measKey.split("_")[1]) 
				with PdfPages(os.path.join(outDir,outFile)) as pdf:
					pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
					pdf.savefig(fig1, bbox_inches='tight', pad_inches=0.2*cm)
				plt.close(fig0)
				plt.close(fig1)



	#Fitted parameters for all channels are shown on plots
	########################################################################################################
	def plotBaselineParams(self,measName=None,extOutName=""):
		selectedMeas = self.selectedMeasurements(self.measBaseID,measName)
		if extOutName != "": extOutName = "_" + extOutName
		for feb in self.Febs:
			cm=1.0/2.54
			fig0,axs = plt.subplots(2,1,figsize=(20*cm,18*cm))
			
			axsLim={0:[],1:[]}
			self.Febs[feb].log("Plotting baseline params: %s"%((", ".join(selectedMeas[feb])).replace(self.measBaseID,"")),"blue",0)
			if len(selectedMeas[feb])==0: continue
			errNotes=[]
			errPoints=[]
			for measKey in selectedMeas[feb]:
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measBaseID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				#inputData = self.Febs[feb].measData[measKey]
				
				for ch in fittedData:
					if fittedData[ch]["baseNotes"] == []: continue
					if not ch in errPoints: errPoints.append(ch)
					for bnote in fittedData[ch]["baseNotes"]:
						if not bnote in errNotes: errNotes.append(bnote)
				
				#print(str([round(fittedData[ch]["baseVal"],4) for ch in sorted(fittedData.keys())]).strip(" []"))
				
				Channels = array([ch for ch in sorted(fittedData.keys())])
				BaseRawVals = array([fittedData[ch]["baseVal"] for ch in sorted(fittedData.keys())])
				BaseSettings = array([fittedData[ch]["baseSetting"] for ch in sorted(fittedData.keys())])
				#limit values for plot yrange customization
				axsLim[0]+=[max(BaseRawVals),min(BaseRawVals)]
				axsLim[1]+=[max(BaseSettings),min(BaseSettings)]
				
				axs[0].plot(Channels,BaseRawVals,"o:",linewidth=0.5, label=measKey.replace(self.measBaseID,""))
				axs[1].plot(Channels,BaseSettings,"o:",linewidth=0.5, label=measKey.replace(self.measBaseID,""))

			txt="\n".join(errNotes)
			axs[0].text(0.985, 0.03, txt, verticalalignment='bottom', horizontalalignment='right', 
													transform=axs[0].transAxes, bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 2},fontsize=7) #color='green',fontsize=15
			
			axs[0].plot(errPoints, [BaseRawVals[ch] for ch in errPoints], marker="o", markersize=15, markeredgecolor="red", markerfacecolor="none")
			axs[0].legend(ncol=5,loc="upper center")
			axs[0].grid()
			axs[0].set_ylim(min(axsLim[0])-2.0,max(axsLim[0])+3.0)
			axs[0].set_xlabel("Channel number [-]")
			axs[0].set_ylabel("Baseline Raw [LSB]")
			
			axs[1].plot(errPoints, [BaseSettings[ch] for ch in errPoints], marker="o", markersize=15, markeredgecolor="red", markerfacecolor="none")
			axs[1].legend(ncol=5,loc="upper center")
			axs[1].grid()
			axs[1].set_ylim(min(axsLim[1])-2.0,max(axsLim[1])+3.0)
			axs[1].set_xlabel("Channel number [-]")
			axs[1].set_ylabel("Baseline Setting [LSB]")
			
			#outFile = "%s_%s_%s"%(self.Febs[feb].userID,measKey,"params.png") 
			#plt.savefig(os.path.join(self.outDir,outFile),bbox_inches='tight') 
				
			outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
			outFile = "%s_%s.pdf"%(self.Febs[feb].userID,self.measBaseID+"Params"+extOutName) 
			axs[1].text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs[1].transAxes, rotation=90, fontsize=6,alpha=0.4)
			
			with PdfPages(os.path.join(outDir,outFile)) as pdf:
				pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
			plt.close(fig0)



	#Fitted parameters for all channels are shown on plots
	########################################################################################################
	def plotThresholdScanParams(self,measName=None,extOutName=""):
		selectedMeas = self.selectedMeasurements(self.measBaseThID,measName)
		if extOutName != "": extOutName = "_" + extOutName
		for feb in self.Febs:
			cm=1.0/2.54
			fig0,axs = plt.subplots(2,1,figsize=(20*cm,18*cm))
			
			axsLim={0:[],1:[]}
			self.Febs[feb].log("Plotting threshold scan params: %s"%((", ".join(selectedMeas[feb])).replace(self.measBaseThID,"")),"blue",0)
			if len(selectedMeas[feb])==0: continue
			errNotes=[]
			errPoints=[]
			for measKey in selectedMeas[feb]:
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measBaseThID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				#inputData = self.Febs[feb].measData[measKey]
			
				for ch in fittedData:
					if fittedData[ch]["thNotes"] == []: continue
					if not ch in errPoints: errPoints.append(ch)
					for bnote in fittedData[ch]["thNotes"]:
						if not bnote in errNotes: errNotes.append(bnote)
			
				Channels = array([ch for ch in sorted(fittedData.keys())])
				ThRawVals = array([fittedData[ch]["thVal"] for ch in sorted(fittedData.keys())])
				ThErr = array([fittedData[ch]["thErr"] for ch in sorted(fittedData.keys())])
				#limit values for plot yrange customization
				axsLim[0]+=[max(ThRawVals),min(ThRawVals)]
				axsLim[1]+=[max(ThErr),min(ThErr)]
				
				axs[0].plot(Channels,ThRawVals,"o:",linewidth=0.5, label=measKey.replace(self.measBaseThID,""))
				axs[1].plot(Channels,ThErr,"o:",linewidth=0.5, label=measKey.replace(self.measBaseThID,""))
			
			
			txt="\n".join(errNotes)
			axs[0].text(0.985, 0.03, txt, verticalalignment='bottom', horizontalalignment='right', 
													transform=axs[0].transAxes, bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 2},fontsize=7) #color='green',fontsize=15
			
			axs[0].plot(errPoints, [ThRawVals[ch] for ch in errPoints], marker="o", markersize=15, markeredgecolor="red", markerfacecolor="none")
			axs[0].legend(ncol=5,loc="upper center")
			axs[0].grid()
			axs[0].set_ylim(min(axsLim[0])-0.5,max(axsLim[0])+0.5)
			axs[0].set_xlabel("Channel number [-]")
			axs[0].set_ylabel("Threshold Raw [LSB]")
			
			axs[1].plot(errPoints, [ThErr[ch] for ch in errPoints], marker="o", markersize=15, markeredgecolor="red", markerfacecolor="none")
			axs[1].legend(ncol=5,loc="upper center")
			axs[1].grid()
			axs[1].set_ylim(min(axsLim[1])-0.25,max(axsLim[1])+0.25)
			axs[1].set_xlabel("Channel number [-]")
			axs[1].set_ylabel("Threshold Error [LSB]")
			
			#outFile = "%s_%s_%s"%(self.Febs[feb].userID,measKey,"params.png") 
			#plt.savefig(os.path.join(self.outDir,outFile),bbox_inches='tight') 
				
			outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
			outFile = "%s_%s.pdf"%(self.Febs[feb].userID,self.measBaseThID+"Params"+extOutName) 
			axs[1].text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs[1].transAxes, rotation=90, fontsize=6,alpha=0.4)
			
			with PdfPages(os.path.join(outDir,outFile)) as pdf:
				pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
			plt.close(fig0)


	#-------------------------------------
	#        Ploting Functions - comparison for all Febs
	#--------------------------------------

	#Fitted parameters for all channels are shown on plots
	#All FEB's in one plot
	########################################################################################################
	def plotThresholdScanParamsCompare(self,measName=None):
		selectedMeas = self.selectedMeasurements(self.measBaseThID,measName)
		selectedMeasFlat=[]
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				if not measKey in selectedMeasFlat: selectedMeasFlat.append(measKey)
		for measKey in selectedMeasFlat:
			printc("Plotting threshold scan comparison for measurement: %s"%(measKey.replace(self.measBaseThID,"")),"blue",0)
			cm=1.0/2.54
			fig0,axs = plt.subplots(2,1,figsize=(20*cm,15*cm))
			
			axsLim={0:[],1:[]}
			for feb in self.Febs:
				self.Febs[feb].log("Plotting threshold scan comparison for measurement: %s"%(measKey.replace(self.measBaseThID,"")),"blue",0, False)
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measBaseThID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				#inputData = self.Febs[feb].measData[measKey]
			
				Channels = array([ch for ch in sorted(fittedData.keys())])
				ThRawVals = array([fittedData[ch]["thVal"] for ch in sorted(fittedData.keys())])
				ThErr = array([fittedData[ch]["thErr"] for ch in sorted(fittedData.keys())])
				#limit values for plot yrange customization
				axsLim[0]+=[max(ThRawVals),min(ThRawVals)]
				axsLim[1]+=[max(ThErr),min(ThErr)]
				
				axs[0].plot(Channels,ThRawVals,"o:",linewidth=0.5, label=self.Febs[feb].userID)
				axs[1].plot(Channels,ThErr,"o:",linewidth=0.5, label=self.Febs[feb].userID)
			
			
			axs[0].legend(ncol=4,loc="upper center")
			axs[0].grid()
			axs[0].set_ylim(min(axsLim[0])-1.0,max(axsLim[0])+1.0)
			axs[0].set_xlabel("Channel number [-]")
			axs[0].set_ylabel("Threshold Raw [LSB]")
			
			axs[1].legend(ncol=4,loc="upper center")
			axs[1].grid()
			axs[1].set_ylim(min(axsLim[1])-0.5,max(axsLim[1])+0.5)
			axs[1].set_xlabel("Channel number [-]")
			axs[1].set_ylabel("Threshold Error [LSB]")
			
			outDir = os.path.join(ReportsPath) 
			outFile = "%s_%s_%s_%s.pdf"%("FEBsCompare",measKey.split("_")[0],"Params",measKey.split("_")[1]) 
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
	Feb = PANDAfeb(0,"E070",True) #creating object as data reader only
	Feb2 = PANDAfeb(0,"E071",True) #creating object as data reader only
	
	Febs={0:Feb}#,1:Feb2}
	
	baseMeas = measBaseline(None,None,None,Febs)
	
	#---------- baselines -------------------
	#baseMeas.fitBaselineData()
	#baseMeas.plotBaselineDetails()
	#baseMeas.plotBaselineParams()
	
	#baseMeas.plotBaselineParams("Simple2","bsimple2") #plot example with custom extended name and selected meas names to plot
	
	#baselines = baseMeas.getBaselineSettings("Simple","Center")
	#printdict(baselines)
	
	#print(Febs[0].measData["Base_1mV20ns"])
	
	#---------- Th Scan ---------------------
	#baseMeas.fitThresholdScanData()
	print(Febs[0].fittedData["BaseTh_1mV20ns"])
	baseMeas.plotThresholdScanParams()
	baseMeas.plotThresholdScanParamsCompare()
	

	

