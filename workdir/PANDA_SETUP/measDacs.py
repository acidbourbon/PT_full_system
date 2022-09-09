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
class measDacs():
	#set font size of plot
	plt.rc('lines', linewidth=1, markersize=2)
	plt.rc('font', size=8)
	plt.rc('axes', prop_cycle=plotCycler)
	#MeasID will be added to Meas name for better measurements type recognizing
	measDacBaseID="DacBase_" 
	measDacThID="DacTh_" 
	
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
				
				
	#Function converts fitted data from specify measDacBaseID measurement to list for baseline setting function in FEB
	#returns dictionary {feb1:[16*baseVal],feb2:[16*baseVal],...}
	#When optional argument Normalization is True, all baselines settings will be shifted to 
	#the highest posible values keeping baseline corrections
	########################################################################################################
	def getBaselineSettings(self, measName, Normalization="Center"):
		baselines={}
		for feb in self.Febs:
			basevals = [0]*16
			if not self.measDacBaseID+measName in self.Febs[feb].fittedData.keys(): continue
			#aAsics = self.Febs[feb].activeAsics
			#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16))
			activeChns = self.Febs[feb].activeChannels
			for ch in activeChns:
				basevals[ch] = self.Febs[feb].fittedData[self.measDacBaseID+measName][ch]["baseSetting"]
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
	
	
	#Function perform measuremnts of Baselie DACs for all FEBs
	#measData are stored directly in FEBs dictionaries
	########################################################################################################
	def runBaselineDacTest(self,measName): 
		stime = datetime.datetime.now() 
		printc("Baseline DAC test for FEBs: %s started at: %s"%(str(list(self.Febs.keys())),stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0)
		measKey=self.measDacBaseID+measName
		
		#setting Th for all febs:
		printc("Setting threshold: %d"%(24),"purple",0)
		for feb in self.Febs:
			self.Febs[feb].setThreshold(24)
		
		#initialize output data dictionaries in FEbs
		for feb in self.Febs: 
			self.Febs[feb].log("Baseline DAC test started at: %s"%(stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0,False)
			info = self.Febs[feb].getFullConfiguration()
			del info["base"]
			#del info["vth"]
			info["date"] = stime.strftime("%d.%m.%Y %H:%M:%S")
			self.Febs[feb].measData[measKey] = {"info":info}
			for ch in range(16):
				self.Febs[feb].measData[measKey][ch]={"B":[],"V":[]}
		
		#Setting generator, constant amplitude and frequency
		self.gen.set_amplitude((1,2),5.0)
		self.gen.set_frequency((1,2),50.0) #50Hz
		self.gen.set_output_state((1,2),True)
		
		self.DataReader.setTriggerEnabled(True)
		
		progress=0.0
		for ch in range(8):
			self.Injectors.setActiveChannel(ch)
			printc("Charge injected to channels: %d and %d"%(ch,ch+8),"purple",0)
			for feb in self.Febs: self.Febs[feb].log("Charge injected to channels: %d and %d"%(ch,ch+8),"purple",0,False)
			
			time.sleep(1.0)
			
			for baseVal in range(32):
				progress+=1.0
				printc("Setting baselines: %s"%(str([baseVal]*16)),"purple",0)
				for feb in self.Febs:
					self.Febs[feb].setBaselines([baseVal]*16)
				time.sleep(0.8) #0.8
				
				tots=self.DataReader.readToT() 
				
				txt=""
				for feb in self.Febs: 
					tot={0:0.0, 8:0.0} #tot for both channels injected in parallel
					for t in tot:
						if 16*feb+ch+t in tots.keys(): tot[t] = round(tots[16*feb+ch+t],3)
						if tot[t]>300.0: tot[t]=300.0 
						if tot[t]<0.0: tot[t]=0.0
						self.Febs[feb].measData[measKey][ch+t]["B"].append(baseVal)
						self.Febs[feb].measData[measKey][ch+t]["V"].append(tot[t])
						
					txt+="%d:[%0.2f,%0.2f] "%(feb,tot[0],tot[8])
					self.Febs[feb].log("TOT: [%0.2f,%0.2f] [ns]"%(tot[0],tot[8]),"green",1,False)
				printc(txt+" [ns] (%0.1f%% done)"%(progress/256*100),"green",1)
					

		self.DataReader.setTriggerEnabled(False)
		#disable all injector channels after mesurements 
		self.Injectors.setActiveChannel(None)
		self.gen.set_output_state((1,2),False)
		etime = datetime.datetime.now() 
		printc("Baseline DAC test for FEBs: %s took: %s"%(str(list(self.Febs.keys())),str(etime-stime).split(".")[0]),"blue",0)
		for feb in self.Febs: self.Febs[feb].log("Baseline DAC test took: %s"%(str(etime-stime).split(".")[0]),"blue",0,False)
		
		return True



	#Function perform measuremnts of Threshold DACs for all FEBs
	#measData are stored directly in FEBs dictionaries
	########################################################################################################
	def runThresholdDacTest(self,measName): 
		stime = datetime.datetime.now() 
		printc("Threshold DAC test for FEBs: %s started at: %s"%(str(list(self.Febs.keys())),stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0)
		measKey=self.measDacThID+measName
		
		#setting Baselines for all febs:
		printc("Setting baselines: %s"%(str([0]*16)),"purple",0)
		for feb in self.Febs:
			self.Febs[feb].setBaselines([0]*16)
		
		#initialize output data dictionaries in FEbs
		for feb in self.Febs: 
			self.Febs[feb].log("Threshold DAC test started at: %s"%(stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0,False)
			info = self.Febs[feb].getFullConfiguration()
			#del info["base"]
			del info["vth"]
			info["date"] = stime.strftime("%d.%m.%Y %H:%M:%S")
			self.Febs[feb].measData[measKey] = {"info":info}
			for ch in range(16):
				self.Febs[feb].measData[measKey][ch]={"T":[],"V":[]}
		
		#Setting generator, constant amplitude and frequency
		self.gen.set_amplitude((1,2),5.0)
		self.gen.set_frequency((1,2),50.0) #50Hz
		self.gen.set_output_state((1,2),True)
		
		self.DataReader.setTriggerEnabled(True)
		
		progress=0.0
		for ch in range(8):
			self.Injectors.setActiveChannel(ch)
			printc("Charge injected to channels: %d and %d"%(ch,ch+8),"purple",0)
			for feb in self.Febs: self.Febs[feb].log("Charge injected to channels: %d and %d"%(ch,ch+8),"purple",0,False)
			
			time.sleep(1.0)
			
			for thVal in range(128):
				progress+=1.0
				printc("Setting threshold: %d"%(thVal),"purple",0)
				for feb in self.Febs:
					self.Febs[feb].setThreshold(thVal)
				time.sleep(0.5)
				
				tots=self.DataReader.readToT() 
				
				txt=""
				for feb in self.Febs: 
					tot={0:0.0, 8:0.0} #tot for both channels injected in parallel
					for t in tot:
						if 16*feb+ch+t in tots.keys(): 
							tot[t] = round(tots[16*feb+ch+t],3)
							if tot[t]>300.0 or tot[t]<10.0: continue
							self.Febs[feb].measData[measKey][ch+t]["T"].append(thVal)
							self.Febs[feb].measData[measKey][ch+t]["V"].append(tot[t])
						
					txt+="%d:[%0.2f,%0.2f] "%(feb,tot[0],tot[8])
					self.Febs[feb].log("TOT: [%0.2f,%0.2f] [ns]"%(tot[0],tot[8]),"green",1,False)
				printc(txt+" [ns] (%0.1f%% done)"%(progress/1024*100),"green",1)
					

		self.DataReader.setTriggerEnabled(False)
		#disable all injector channels after mesurements 
		self.Injectors.setActiveChannel(None)
		self.gen.set_output_state((1,2),False)
		etime = datetime.datetime.now() 
		printc("Threshold DAC test for FEBs: %s took: %s"%(str(list(self.Febs.keys())),str(etime-stime).split(".")[0]),"blue",0)
		for feb in self.Febs: self.Febs[feb].log("Threshold DAC test took: %s"%(str(etime-stime).split(".")[0]),"blue",0,False)
		
		return True



	#-------------------------------------
	#        Fitting and calculations Functions
	#--------------------------------------


	#Function calculate parameters from baseline DAC measurements
	#Calculated parameters are stored in fittedData dictionary in FEB
	########################################################################################################
	def fitBaselineDacData(self,measName=None):
		retval = True
		selectedMeas = self.selectedMeasurements(self.measDacBaseID,measName)
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Calculating baseline DACs parameters from: %s"%(measKey.replace(self.measDacBaseID,"")),"blue",0)
				#fittedData[measBaseID+measName][ch:{baseVal:val, baseSetting: val, ...},ch:{baseVal:val, baseSetting: val, ...}]
				self.Febs[feb].fittedData[measKey]={}
				inputData = self.Febs[feb].measData[measKey]
				#aAsics = self.Febs[feb].activeAsics
				#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16))
				activeChns = self.Febs[feb].activeChannels
				TOTsBase15=[]
				for ch in activeChns:
					idx15=inputData[ch]["B"].index(15)
					TOTsBase15.append(inputData[ch]["V"][idx15])
					
				for ch in activeChns:
					BaseVal = inputData[ch]["B"]
					TOTs = inputData[ch]["V"]
					try:
						ArBaseVal = array([float(b) for b in BaseVal])
						ArTOTs = array([float(c) for c in TOTs])
						ArTOTderiv = ArTOTs[1:] - ArTOTs[:-1] #Calculate simple derivative (next - previous value)
						#Checking derivative vales and limits the range if something is wrong
						for nlim in [1,2,3,4,5,6,7,8]:
							if min(ArTOTderiv)<0 or max(ArTOTderiv)>2*average(ArTOTderiv[4:-4]): 
								ArTOTderiv = ArTOTs[1:-nlim] - ArTOTs[:-nlim-1]
							else: break
							#print(ch, ArTOTderiv, min(ArTOTderiv),average(ArTOTderiv[4:-4]))
						#Calculate the absolute value from (TOT-average) to get baseline settings from TOT
						ArTOTsDiff = abs(ArTOTs - mean(TOTsBase15))
						base = int(argmin(ArTOTsDiff)) #minimum value index gives the best baseline setting
						self.Febs[feb].fittedData[measKey][ch]={"baseSetting":base, "base15TOTave":float(mean(TOTsBase15)), "baseTOTdnl":around(ArTOTderiv, decimals=4).tolist()}
					except:
						e = sys.exc_info()[0]
						self.Febs[feb].fittedData[measKey][ch]={"baseSetting":0, "base15TOTave":0.0, "baseTOTdnl":[]}
						self.Febs[feb].log("fitBaselineDacData error: %s"%e.__name__,"red",0)
						retval = False

		return retval


	#Function calculate parameters from Threshold DAC measurements
	#Calculated parameters are stored in fittedData dictionary in FEB
	########################################################################################################
	def fitThresholdDacData(self,measName=None):
		retval = True
		selectedMeas = self.selectedMeasurements(self.measDacThID,measName)
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Calculating Threshold DAC parameters from: %s"%(measKey.replace(self.measDacThID,"")),"blue",0)
				#fittedData[measBaseID+measName][ch:{baseVal:val, baseSetting: val, ...},ch:{baseVal:val, baseSetting: val, ...}]
				self.Febs[feb].fittedData[measKey]={}
				inputData = self.Febs[feb].measData[measKey]
				#aAsics = self.Febs[feb].activeAsics
				#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16))
				activeChns = self.Febs[feb].activeChannels
				for ch in activeChns:
					ThVal = inputData[ch]["T"]
					TOTs = inputData[ch]["V"]
					try:
						ArThVal = array([float(b) for b in ThVal])
						ArTOTs = array([float(c) for c in TOTs])
						ArTOTderiv = ArTOTs[1:] - ArTOTs[:-1] #Calculate simple derivative (next - previous value)
						#Checking derivative vales and limits the range if something is wrong
						for nlim in [1,2,3,4]:
							if max(ArTOTderiv)>0 or min(ArTOTderiv)<5*average(ArTOTderiv[10:-10]): 
								ArTOTderiv = ArTOTs[1:-nlim] - ArTOTs[:-nlim-1]
							else: break
							#print(ch, ArTOTderiv, max(ArTOTderiv),5*average(ArTOTderiv[10:-10]))
						self.Febs[feb].fittedData[measKey][ch]={"thTOTdnl":around(ArTOTderiv, decimals=4).tolist()}
					except:
						e = sys.exc_info()[0]
						self.Febs[feb].fittedData[measKey][ch]={"thTOTdnl":[]}
						self.Febs[feb].log("fitThresholdDacData error: %s"%e.__name__,"red",0)
						retval = False
		return retval


	#-------------------------------------
	#        Ploting Functions
	#--------------------------------------

	
	########################################################################################################
	def plotBaselineDacsCurves(self,measName=None):
		selectedMeas = self.selectedMeasurements(self.measDacBaseID,measName)
		for feb in self.Febs:
			self.Febs[feb].log("Plotting baseline DACs TOT curves: %s"%((", ".join(selectedMeas[feb])).replace(self.measDacBaseID,"")),"blue",0)
			for measKey in selectedMeas[feb]:
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measDacBaseID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				inputData = self.Febs[feb].measData[measKey]
				#aAsics = self.Febs[feb].activeAsics
				#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16))
				activeChns = self.Febs[feb].activeChannels
				cm=1.0/2.54
				fig0,axs = plt.subplots(2,1,figsize=(20*cm,25*cm),gridspec_kw={'height_ratios': [2, 1]})
				
				for ch in activeChns:
					if not ch in inputData.keys(): continue
					#Getting input data for plot
					Base = inputData[ch]["B"]
					Tot = inputData[ch]["V"] 
					TotAV = fittedData[ch]["base15TOTave"] #Should be the same for all measured channels
					axs[0].plot(Base,Tot,"-", label="Channel %02d"%(ch))
					
				#Plotting horizontal TOT average line
				axs[0].plot(Base,[TotAV]*len(Base),"k--",linewidth=0.5) #, label="TOT average"
				
				MaxBaseSett=0
				MaxTotSett=0.0
				
				axs[0].set_prop_cycle(plotCycler)
				for ch in activeChns:
					if not ch in inputData.keys(): continue
					#Getting input data for plot
					BaseSett = fittedData[ch]["baseSetting"]
					TotSett = inputData[ch]["V"][BaseSett]
					if BaseSett > MaxBaseSett:
						MaxBaseSett=BaseSett
						MaxTotSett = TotSett
					axs[0].plot(BaseSett,TotSett,"o",markersize=3)#, label="Channel %02d"%(ch))
					
				axs[0].annotate('Dots: TOT based\nBaseline corrections', xy=(MaxBaseSett, MaxTotSett), xytext=(0.85, 0.1), textcoords=axs[0].transAxes, va="top", ha="center",
									bbox=dict(boxstyle="round", alpha=0.4, facecolor='green'),
									arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2"),)
				axs[0].set_xlim(0,32)
				axs[0].legend(ncol=2, loc="upper left", fontsize='x-small')
				axs[0].grid()
				axs[0].set_xlabel("Baseline Setting [LSB]")
				axs[0].set_ylabel("TOT [ns]")
				
				for ch in activeChns:
					if not ch in inputData.keys(): continue
					#Getting input data for plot
					TotDeriv = fittedData[ch]["baseTOTdnl"]
					Base = inputData[ch]["B"][:len(TotDeriv)] #unused values should be skipped according to derivative data which may have limited points
					
					#axs[1].plot(Base,TotDeriv,"-", label="Channel %02d"%(ch))
					axs[1].step(Base,TotDeriv, where='post', label="Channel %02d"%(ch))
				
				axs[1].set_xlim(0,32)
				axs[1].legend(ncol=4, loc="upper left", fontsize='x-small')
				axs[1].grid()
				axs[1].set_xlabel("Baseline Setting [LSB]")
				axs[1].set_ylabel("TOT DNL [ns]")
				
				outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
				outFile = "%s_%s_%s_%s.pdf"%(self.Febs[feb].userID,measKey.split("_")[0],"DacsCurves",measKey.split("_")[1]) 
				axs[1].text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs[1].transAxes, rotation=90, fontsize=6,alpha=0.4)
				
				with PdfPages(os.path.join(outDir,outFile)) as pdf:
					pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
				plt.close(fig0)



	########################################################################################################
	def plotThresholdDacsCurves(self,measName=None):
		selectedMeas = self.selectedMeasurements(self.measDacThID,measName)
		for feb in self.Febs:
			self.Febs[feb].log("Plotting threshold DACs TOT curves: %s"%((", ".join(selectedMeas[feb])).replace(self.measDacThID,"")),"blue",0)
			for measKey in selectedMeas[feb]:
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measDacThID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				inputData = self.Febs[feb].measData[measKey]
				#aAsics = self.Febs[feb].activeAsics
				#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16))
				activeChns = self.Febs[feb].activeChannels
				cm=1.0/2.54
				fig0,axs = plt.subplots(2,1,figsize=(20*cm,25*cm),gridspec_kw={'height_ratios': [2, 1]})
				
				for ch in activeChns:
					if not ch in inputData.keys(): continue
					#Getting input data for plot
					Vth = inputData[ch]["T"]
					Tot = inputData[ch]["V"]
					axs[0].plot(Vth,Tot,"-", label="Channel %02d"%(ch))

				axs[0].set_xlim(0,128)
				axs[0].legend(ncol=4, loc="lower left", fontsize='x-small')
				axs[0].grid()
				axs[0].set_xlabel("Threshold Setting [LSB]")
				axs[0].set_ylabel("TOT [ns]")
				
				for ch in activeChns:
					if not ch in inputData.keys(): continue
					#Getting input data for plot
					TotDeriv = fittedData[ch]["thTOTdnl"]
					Vth = inputData[ch]["T"][:len(TotDeriv)] #unused values should be skipped according to derivative data which may have limited points
					#axs[1].plot(Vth,TotDeriv,"-", label="Channel %02d"%(ch))
					axs[1].step(Vth,TotDeriv, where='post', label="Channel %02d"%(ch))
				
				axs[1].set_xlim(0,128)
				axs[1].legend(ncol=4, loc="lower left", fontsize='x-small')
				axs[1].grid()
				axs[1].set_xlabel("Threshold Setting [-]")
				axs[1].set_ylabel("TOT DNL [ns]")
				
				outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
				outFile = "%s_%s_%s_%s.pdf"%(self.Febs[feb].userID,measKey.split("_")[0],"DacsCurves",measKey.split("_")[1]) 
				axs[1].text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs[1].transAxes, rotation=90, fontsize=6,alpha=0.4)
				
				with PdfPages(os.path.join(outDir,outFile)) as pdf:
					pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
				plt.close(fig0)
	#-------------------------------------
	#        Ploting Functions - comparison for all Febs
	#--------------------------------------

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
	
	dacMeas = measDacs(None,None,None,Febs)
	
	dacMeas.fitBaselineDacData("Test1")
	dacMeas.fitThresholdDacData("Test1")
	
	dacMeas.plotBaselineDacsCurves("Test1")
	dacMeas.plotThresholdDacsCurves("Test1")
	
	
	#print(Febs[0].fittedData)
	print(dacMeas.getBaselineSettings("Test1","Center"))
	#print(dacMeas.getBaselineSettings("Test2","Center"))
	#print(dacMeas.getBaselineSettings("Test3","Center"))
	

