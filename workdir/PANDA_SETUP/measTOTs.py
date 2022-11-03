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
import pasttrec_ctrl as pasttrec_ctrl

sys.path.append(os.path.split(os.path.realpath(__file__))[0]+"/Devices")

from config import *



colorList = ["#FF0000","#00FF00","#0000FF","#FFFF00","#993300","#339900","#0288d1","#fbc02d","#f06292","#c0ca33","#4db6ac","#ff7043","#ab47bc","#795548","#90a4ae","#000000"]
plotCycler = cycler(color=colorList)

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class measTOTs():
	#set font size of plot
	plt.rc('lines', linewidth=1, markersize=2)
	plt.rc('font', size=8)
	plt.rc('axes', prop_cycle=plotCycler)
	#MeasID will be added to Meas name for better measurements type recognizing
	measTOTsID="TOTs_" 
	
	
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
				
				
	#--------------- ----------------------
	#        Measurements Functions
	#--------------------------------------
	
	#Function run TOT scan measurement for all FEB's given as class argument
	########################################################################################################
	def runTOTsScan(self,measName,injChns=None):
		#enabel trigger (pulser0)
		#os.system("trbcmd w 0xc001 0xa101 0xffff0002")
		stime = datetime.datetime.now() 
		printc("TOT Scan for FEBs: %s started at: %s"%(str(list(self.Febs.keys())),stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0)
		measKey=self.measTOTsID+measName
		StartAmp = 0.1
		step = 0.2
		
		if injChns == None: injChns = list(range(0,8))
		
		#initialize output data dictionaries in FEbs
		for feb in self.Febs: 
			self.Febs[feb].log("TOT Scan started at: %s"%(stime.strftime("%d.%m.%Y %H:%M:%S")),"blue",0,False)
			info = self.Febs[feb].getFullConfiguration()
			info["date"] = stime.strftime("%d.%m.%Y %H:%M:%S")
			self.Febs[feb].measData[measKey] = {"info":info}
			for ch in injChns:
				self.Febs[feb].measData[measKey][ch]={"A":[],"V":[],"Verr":[],"convFactor": self.Febs[feb].convFactors[ch]}
				#self.Febs[feb].measData[measKey][ch+8]={"A":[],"V":[],"convFactor": self.Febs[feb].convFactors[ch+8]}

		#Setting generator, starting amplitude and frequency
		self.gen.set_amplitude((1,2),StartAmp)
		self.gen.set_frequency((1,2),1000) #50Hz
		self.gen.set_output_state((1,2),True)

		self.DataReader.setTriggerEnabled(True)
		
		for ch in injChns:
			self.Injectors.setActiveChannel(ch)
			printc("Charge injected to channels: %d and %d"%(ch,ch+8),"purple",0)
			for feb in self.Febs: self.Febs[feb].log("Charge injected to channels: %d and %d"%(ch,ch+8),"purple",0,False)
			#Thresholds = [ 30 ]
			#for th in Thresholds:
				#pasttrec_ctrl.set_threshold_for_board_by_name("4000",th)
			amp = StartAmp
			self.gen.set_amplitude((1,2),amp) #Setting start amplitude -  to be sure that proper value is set before measurements starts

			#time.sleep(1.0)

			while(1):
				self.gen.set_amplitude((1,2),amp)
				#time.sleep(0.8)
			
				(tots,stdev)=self.DataReader.readToT(50) #slightly worst precision 0.5->0.75ns ~around 1% precision 
				txt="A: %0.3f[V]  "%(round(amp,3))
				for feb in self.Febs: 
					tot={0:0.0} #tot one  channel injected  
					#tot={0:0.0, 8:0.0} #tot for both channels injected in parallel					
					for t in tot:
						if 16*feb+ch+t in tots.keys(): 
							tot[t] = round(tots[16*feb+ch+t],3)
							if tot[t]>500.0: tot[t]=500.0 
							if tot[t]<0.0: tot[t]=0.0
							self.Febs[feb].measData[measKey][ch+t]["A"].append(round(amp,3))
							self.Febs[feb].measData[measKey][ch+t]["V"].append(tot[t])
							self.Febs[feb].measData[measKey][ch+t]["Verr"].append(stdev)
					txt+="%d:[%0.2f] "%(feb,tot[0] )
					self.Febs[feb].log("A: %0.3f[V]  TOT: [%0.2f ] [ns]"%(round(amp,3),tot[0] ),"green",1,False)
				printc(txt+" [ns]","green",1)
				
				amp+=step
				if amp > 5.0: break
					
		self.DataReader.setTriggerEnabled(False)
		self.gen.set_output_state((1,2),False)
		#self.Injectors.setActiveChannel(7)
		#self.gen.set_amplitude((1,2),5.0)
		etime = datetime.datetime.now() 
		printc("TOT Scan for FEBs: %s took: %s"%(str(list(self.Febs.keys())),str(etime-stime).split(".")[0]),"blue",0)
		for feb in self.Febs: self.Febs[feb].log("TOT Scan took: %s"%(str(etime-stime).split(".")[0]),"blue",0,False)
		return True
		


	#-------------------------------------
	#        Fitting and calculations Functions
	#--------------------------------------
	
	
	#Function fits polynomials to all channels. 
	#Calculated parameters are stored in fittedData dictionary in FEB
	########################################################################################################
	def fitTOTsData(self,measName=None):
		retval = True
		selectedMeas = self.selectedMeasurements(self.measTOTsID,measName)
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Fitting TOT curves to: %s"%(measKey.replace(self.measTOTsID,"")),"blue",0)
				#fittedData[measTOTsID+measName][ch:{sigma:val, median: val, ...},ch:{sigma:val, median: val, ...}]
				self.Febs[feb].fittedData[measKey]={}
				inputData = self.Febs[feb].measData[measKey]
				#aAsics = self.Febs[feb].activeAsics #active channels, it will be limited if one of the asic doesn't answer
				#activeChns = list(range(8*aAsics[0],8*aAsics[0]+8)) if len(aAsics)==1 else list(range(0,16)) 
				activeChns = self.Febs[feb].activeChannels
				for ch in inputData:
					if ch == "info": continue
					if not ch in activeChns: continue
					Amp = inputData[ch]["A"]
					Tot = inputData[ch]["V"]
					convFactor = inputData[ch]["convFactor"]
					try:
						Qin = array([float(a) * convFactor for a in Amp])
						#Qin = array([float(a) * 1. for a in Amp])
						ArTot = array([float(t) for t in Tot])
						#standart reverted fit tot->charge
						polyOrder = 5
						p = polyfit(ArTot, Qin, polyOrder)
						self.Febs[feb].fittedData[measKey][ch]={"polyCoeff":list(p)}
						#straight fit
						#polyOrder2 = 10
						#p = polyfit(Qin,ArTot, polyOrder2)
						#self.Febs[feb].fittedData[measKey][ch]["polyCoeffStraight"]=list(p)
					except:
						e = sys.exc_info()[0]
						self.Febs[feb].fittedData[measKey][ch]={"polyCoeff":[0.0]*polyOrder}
						#self.Febs[feb].fittedData[measKey][ch]={"polyCoeff":[0.0]*polyOrder,"polyCoeffStraight":[0.0]*polyOrder2}
						self.Febs[feb].log("fitTOTsData error: %s"%e.__name__,"red",0)
						retval = False
						
		return retval
		

	
	#-------------------------------------
	#        Ploting Functions for one FEB
	#--------------------------------------
	
	#Function plot TOT measurements data
	########################################################################################################
	def plotTOTsCurves(self,measName=None):
		selectedMeas = self.selectedMeasurements(self.measTOTsID,measName)
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Plotting TOTs Curves: %s"%(measKey.replace(self.measTOTsID,"")),"blue",0)
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measTOTsID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				inputData = self.Febs[feb].measData[measKey]
				#print(fittedData)
				activeChns = self.Febs[feb].activeChannels
				#print(feb,activeChns)
				cm=1.0/2.54
				fig0,axs = plt.subplots(1,1,figsize=(20*cm,26*cm)) #,gridspec_kw={'height_ratios': [2, 1]}
				#fig0,errbar = plt.subplots(1,1,figsize=(20*cm,26*cm)) #,gridspec_kw={'height_ratios': [2, 1]}	
				
				for ch in range(8):
					if not ch in inputData.keys(): continue
					if not ch in activeChns: continue
					#Getting input data for plot
					Amp = inputData[ch]["A"]
					Tot = inputData[ch]["V"]
					Toterr = inputData[ch]["Verr"]
					print("channel ", ch," - STDevs (eachc amplitude): ", Toterr )
					convFactor = inputData[ch]["convFactor"]
					#Qin = array([float(a) * 1 for a in Amp])
					Qin = array([float(a) * convFactor for a in Amp])					
					#Qin = array([float(a) for a in Amp])	
					 
					ArTot = array([float(t) for t in Tot])
					ArTotErr = array([float(t) for t in Toterr])
					axs.plot(Qin,ArTot,"o", label="Channel %02d"%(ch))
					errbar= plt.errorbar(Qin,ArTot,ArTotErr,xerr=None, color=colorList[ch], linestyle=':', label="Channel %02d"%(ch))
				axs.set_prop_cycle(plotCycler)
				 
				txt="Charge = $p5 \cdot TOT^5 + p4 \cdot TOT^4 + p3 \cdot TOT^3 + p2 \cdot TOT^2 + p1 \cdot TOT + p0$\n\n"
				txt+="Fitted coefficients [p5,...,p0] for all channels:\n\n"
				for ch in range(8):
					if not ch in inputData.keys(): continue
					if not ch in activeChns: continue
					#Getting input data for plot
					Tot = inputData[ch]["V"]
					ArTot = array([float(t) for t in Tot])
					#Preparing fitted data for plot
					polyCoeff = fittedData[ch]["polyCoeff"]
					if not ArTot.any(): 
						ArTotPoly = linspace(50,100,150) #y axis for fitted curve plotting
					else:
						ArTotPoly = linspace(min(ArTot ),max(ArTot ),100) #y axis for fitted curve plotting
					
					QinPoly = polyval(polyCoeff, ArTotPoly)
					
					#axs.plot(QinPoly,ArTotPoly,"-",linewidth=0.5)
					#txt+="%02d:  [%0.3e,  %0.3e,  %0.3e,  %0.3e,  %0.3e,  %0.3e]\n"%(ch,*polyCoeff)
				
				txt+="\n*Fitting procedure swaps axes for easy charge calculation (in [$ke^-$]),\n TOT value should be expressed in [ns]"
				#axs.text(0.32, 0.35, txt, verticalalignment='top', horizontalalignment='left', 
													#transform=axs.transAxes, bbox={'facecolor': 'yellow', 'alpha': 0.3, 'pad': 3},fontsize=7) 

				#axs.set_xlim(0,128)
				axs.legend(ncol=1, loc="center right", fontsize='x-small')
				axs.grid()
				axs.set_xlabel("Input charge [$ke^-$]")
				axs.set_ylabel("TOT [ns]")
				
				outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
				outFile = "%s_%s_%s_%s.pdf"%(self.Febs[feb].userID,measKey.split("_")[0],"TOTCurves",measKey.split("_")[1]) 
				axs.text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs.transAxes, rotation=90, fontsize=6,alpha=0.4)
			
				with PdfPages(os.path.join(outDir,outFile)) as pdf:
					pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
					print("PDF saving",outDir,outFile)
				plt.close(fig0)
					

	'''
	#Function plot TOT measurements data with gain normalization
	########################################################################################################
	def plotTOTsGainNormCurves(self,measName=None):
		selectedMeas = self.selectedMeasurements(self.measTOTsID,measName)
		for feb in self.Febs:
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Plotting TOTs Curves: %s"%(measKey.replace(self.measTOTsID,"")),"blue",0)
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measTOTsID,"")),"orange",0)
					continue

				fittedData = self.Febs[feb].fittedData[measKey]
				inputData = self.Febs[feb].measData[measKey]
				#print(fittedData)
				activeChns = self.Febs[feb].activeChannels
				#print(feb,activeChns)
				cm=1.0/2.54
				fig0,axs = plt.subplots(1,1,figsize=(20*cm,26*cm)) #,gridspec_kw={'height_ratios': [2, 1]}
				
				
				#finding center channel
				maxTotsAve = mean([float(inputData[ch]["V"][-1]) for ch in activeChns])
				selCh=0
				MinTotErr=100.0 #starting value
				for ch in range(16):
					if not ch in inputData.keys(): continue
					if not ch in activeChns: continue
					TotErr = abs(inputData[ch]["V"][-1] - maxTotsAve)
					if TotErr < MinTotErr:
						MinTotErr = TotErr
						selCh = ch

				Qin = array([float(a) * inputData[selCh]["convFactor"] for a in inputData[selCh]["A"]])
				normPolyCoeff = fittedData[selCh]["polyCoeffStraight"]
				normArQinPoly = linspace(min(Qin),max(Qin),100) #x axis for fitted curve plotting
				normArTotPoly = polyval(normPolyCoeff, normArQinPoly)
				
				
				axs.set_prop_cycle(plotCycler)
				for ch in range(16):
					if not ch in inputData.keys(): continue
					if not ch in activeChns: continue

					polyCoeff = fittedData[ch]["polyCoeffStraight"]
					ArTotPoly = polyval(polyCoeff, normArQinPoly)
					axs.plot(normArQinPoly,ArTotPoly/normArTotPoly,"-",linewidth=0.8,label="Channel %02d"%(ch))

				#axs.set_xlim(0,128)
				axs.legend(ncol=1, loc="upper right", fontsize='x-small')
				axs.grid()
				axs.set_xlabel("Input charge [$ke^-$]")
				axs.set_ylabel("Normalization factor [-]")
				
				outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
				outFile = "%s_%s_%s_%s_GNorm.pdf"%(self.Febs[feb].userID,measKey.split("_")[0],"TOTCurves",measKey.split("_")[1]) 
				axs.text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs.transAxes, rotation=90, fontsize=6,alpha=0.4)
			
				with PdfPages(os.path.join(outDir,outFile)) as pdf:
					pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
				plt.close(fig0)
					

	#Function plot TOT measurements data
	########################################################################################################
	def plotTOTsThCurves(self,measName=None):
		selectedMeas = self.selectedMeasurements(self.measTOTsID,measName)
		for feb in self.Febs:
			
			activeChns = self.Febs[feb].activeChannels
			#print(feb,activeChns)
			cm=1.0/2.54
			fig0,axs = plt.subplots(1,1,figsize=(20*cm,26*cm)) #,gridspec_kw={'height_ratios': [2, 1]}
			
			selCh=0
			inputData = self.Febs[feb].measData[selectedMeas[feb][-1]]
			fittedData = self.Febs[feb].fittedData[selectedMeas[feb][-1]]
			Qin = array([float(a) * inputData[selCh]["convFactor"] for a in inputData[selCh]["A"]])
			normPolyCoeff = fittedData[selCh]["polyCoeffStraight"]
			normArQinPoly = linspace(min(Qin),max(Qin),100) #x axis for fitted curve plotting
			normArTotPoly = polyval(normPolyCoeff, normArQinPoly)
			
			for measKey in selectedMeas[feb]:
				self.Febs[feb].log("Plotting TOTs Curves: %s"%(measKey.replace(self.measTOTsID,"")),"blue",0)
				if not measKey in self.Febs[feb].fittedData.keys():
					self.Febs[feb].log("There are no fitted data: %s, skipped..."%(measKey.replace(self.measTOTsID,"")),"orange",0)
					continue
				
				fittedData = self.Febs[feb].fittedData[measKey]
				inputData = self.Febs[feb].measData[measKey]
				#print(fittedData)
				
				#axs.set_prop_cycle(plotCycler)
				for ch in [0]:
					if not ch in inputData.keys(): continue
					if not ch in activeChns: continue
					#Getting input data for plot
					Amp = inputData[ch]["A"]
					convFactor = inputData[ch]["convFactor"]
					Qin = array([float(a) * convFactor for a in Amp])
					ArQinPoly = linspace(min(Qin),max(Qin),100) #x axis for fitted curve plotting
					
					polyCoeff = fittedData[ch]["polyCoeffStraight"]
					TotPoly = polyval(polyCoeff, normArQinPoly)
					axs.plot(normArQinPoly,TotPoly/normArTotPoly,"-",linewidth=0.5, label="%s"%(measKey))

			#axs.set_xlim(0,128)
			axs.legend(ncol=1, loc="center right", fontsize='x-small')
			axs.grid()
			axs.set_xlabel("Input charge [$ke^-$]")
			axs.set_ylabel("TOT [ns]")
			
			outDir = os.path.join(ReportsPath,self.Febs[feb].userID)
			outFile = "%s_%s_%s_%s_ThPlot.pdf"%(self.Febs[feb].userID,measKey.split("_")[0],"TOTCurves",measKey.split("_")[1]) 
			axs.text(1.005, 0.0, outFile.strip(".pdf"), verticalalignment='bottom', horizontalalignment='left', transform=axs.transAxes, rotation=90, fontsize=6,alpha=0.4)
		
			with PdfPages(os.path.join(outDir,outFile)) as pdf:
				pdf.savefig(fig0, bbox_inches='tight', pad_inches=0.2*cm)
			plt.close(fig0)
	'''

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------


if __name__=="__main__":
	
	from PANDAfeb import PANDAfeb
	Feb = PANDAfeb(0,"B002",True) #creating object as data reader only
	Feb2 = PANDAfeb(0,"B003",True) #creating object as data reader only
	
	Febs={0:Feb}#,1:Feb2}
	
	TOTsMeas = measTOTs(None,None,None,Febs)
	TOTsMeas.fitTOTsData()

	TOTsMeas.plotTOTsCurves()


	


