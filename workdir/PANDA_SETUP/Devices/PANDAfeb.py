#!/usr/bin/env python3
import os
import time
import sys, tty, termios
import subprocess
import json
import pasttrec_ctrl as pasttrec_ctrl

import bz2
import pickle
import _pickle as cPickle

from config import *

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class PasttrecReg():
	#--------------- ----------------------
	#        INIT and general functions
	#--------------------------------------
	def __init__(self,addr,defVal,testVals,descr):
		self.addr = addr
		self.defVal = defVal
		self.testVals = testVals
		self.descr = descr
	
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class PANDAfeb():
	#--------------- ----------------------
	#        Consts
	#--------------------------------------
	#c_fpga = [0x6441, 0x6442, 0x6443]
	c_fpga = [0x1000]
	c_cable = [0x00 << 19, 0x01 << 19, 0x02 << 19 ]
	c_asic = [0x2000, 0x4000 ]
	#c_trbnet_reg = 0xa000
	c_trbnet_reg = 0xd417
	aRegs={}
	aRegs["PRE"] = PasttrecReg(0x00000, 0x10, [0x15,0x0A],"Preamp configuration register")
	aRegs["TC1"] = PasttrecReg(0x00100, 0x00, [0x2A,0x15], "Tail cancelation 1 register")
	aRegs["TC2"] = PasttrecReg(0x00200, 0x00, [0x2A,0x15], "Tail cancelation 2 register")
	aRegs["VTH"] = PasttrecReg(0x00300, 0x08, [0x55,0x2A], "Global treshold register")
	aRegs["BASE0"] = PasttrecReg(0x00400, 0x0F, [0x15,0x0A], "Baseline trim ch0 register")
	aRegs["BASE1"] = PasttrecReg(0x00500, 0x0F, [0x15,0x0A], "Baseline trim ch1 register")
	aRegs["BASE2"] = PasttrecReg(0x00600, 0x0F, [0x15,0x0A], "Baseline trim ch2 register")
	aRegs["BASE3"] = PasttrecReg(0x00700, 0x0F, [0x15,0x0A], "Baseline trim ch3 register")
	aRegs["BASE4"] = PasttrecReg(0x00800, 0x0F, [0x15,0x0A], "Baseline trim ch4 register")
	aRegs["BASE5"] = PasttrecReg(0x00900, 0x0F, [0x15,0x0A], "Baseline trim ch5 register")
	aRegs["BASE6"] = PasttrecReg(0x00A00, 0x0F, [0x15,0x0A], "Baseline trim ch6 register")
	aRegs["BASE7"] = PasttrecReg(0x00B00, 0x0F, [0x15,0x0A], "Baseline trim ch7 register")
	aRegs["LVDS"] = PasttrecReg(0x00D00, 0x05, [0x03,0x04], "LVDS configuration register")
	
	#--------------- ----------------------
	#        INIT and general functions and private
	#--------------------------------------
	def __init__(self,testBranch,userID, isDataReader=False):
		self.FEBok=True
		self.fpga = int(testBranch/3)
		self.cable = testBranch%3
		self.fpgaAddr = self.c_fpga[self.fpga]
		self.cableAddr = self.c_cable[self.cable]
		self.activeAsics = [0,1]
		self.activeChannels = list(range(0,16))
		self.isDataReader=isDataReader
		self.convFactors=[]
		self.measData={}
		self.fittedData={}
		self.userID=userID
		self.hardID="N/A" #should be placed in measData
		
		#Creating Reports directory id doesn't exists
		outDir = os.path.join(ReportsPath,self.userID)
		if not os.path.exists(outDir):
			os.system("mkdir %s"%outDir)
			self.log("Creating output directory... %s"%outDir,"brown",0)

		self.loadData()
		
		if not "FebInfo" in self.measData.keys():
			self.measData["FebInfo"]={"userID":self.userID}  #initialize the FebInfo data field
			self.log("Missing FebInfo field in measurements data! Ok when board is measured first time","orange",0)
		else:
			if self.measData["FebInfo"]["userID"]!=self.userID:
				self.log("Loaded data doesn't belong to this board. Its comes from board: %s"%self.measData["FebInfo"]["userID"],"red",0)
				sys.exit()
			else:
				if "activeAsics" in self.measData["FebInfo"].keys(): self.activeAsics = self.measData["FebInfo"]["activeAsics"]
				if "activeChannels" in self.measData["FebInfo"].keys(): self.activeChannels = self.measData["FebInfo"]["activeChannels"]
				
		if not self.isDataReader: #disble communication when FEB is defined as data reader only
			self.log("################### ----- FEB: %s (Branch %d), initializing for measurements... ----- ###################"%(self.userID,testBranch),"blue",0)
			self.log("FEB initialized at: %s"%(time.strftime("%d.%m.%Y %H:%M:%S")),"blue",0)
			self.resetAsics()
			#reading hardware ID here, after chip reset
			#login: uasic   pass: UASIC
			
			self.log("Reading hardware ID...  Hardware ID: %s"%(self.hardID),"green",0)
			#os.system("communication_test.py %s:%d"%(hex(self.fpgaAddr),self.cable+1))
			#self.FEBok = self.testAllRegisters()
			self.saveData()
		#print(self.measData["FebInfo"])

		

	#Function writes one register in selected ASIC on FEB board
	def writeReg(self, asic, reg, val):
		v = 0x00050000 | self.cableAddr | self.c_asic[asic] | reg | val
		
		l = [ 'trbcmd', 'w', hex(self.fpgaAddr), hex(self.c_trbnet_reg), hex(v) ]
		rc = subprocess.run(l, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


	#Function reads one register in selected ASIC on FEB board
	def readReg(self, asic, reg):
		v = 0x00051000 | self.cableAddr | self.c_asic[asic] | reg
		
		l = [ 'trbcmd', 'w', hex(self.fpgaAddr), hex(self.c_trbnet_reg), hex(v) ]
		rc = subprocess.run(l, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		l = [ 'trbcmd', 'r', hex(self.fpgaAddr), hex(self.c_trbnet_reg) ]
		rc = subprocess.run(l, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		
		return int(rc.stdout.decode().split()[1],16)


	#Function get configuration (regid = PRE, TC1...) for both asics in FEB, when asic is not specified returns list of 2 values
	def getRegByID(self, regid, asic=None):
		if asic in [0,1]:
			return self.readReg(asic,self.aRegs[regid].addr)
		else:
			ret=[]
			for asic in range(2):
				ret.append(self.readReg(asic,self.aRegs[regid].addr))
			return ret


	#reset both asics on the FEB
	def resetAsics(self):
		self.log("Reseting ASIC's...","green",0)
		pasttrec_ctrl.reset_board(str(self.fpgaAddr),1)		 
		#os.system("reset_asic.py %s:%d"%(hex(self.fpgaAddr),self.cable+1))
	
	
	#load data from data files
	def loadData(self):
		fileexists = False
		#file names for different formats
		fnameCPkl="%s.cdat"%(os.path.join(ResultsPath,self.userID))
		fnamePkl="%s.dat"%(os.path.join(ResultsPath,self.userID))
		fnameJson="%s.json"%(os.path.join(ResultsPath,self.userID))
		#---- Pickle with compresion
		if os.path.exists(fnameCPkl):
			fileexists = True
			if not self.isDataReader: self.log("Warning! FEB with ID: %s was already measured."%(self.userID),"orange",0)
			with bz2.BZ2File(fnameCPkl, 'rb') as outfile:
				data = cPickle.load(outfile)
				self.measData=data["measData"]
				self.fittedData=data["fittedData"]
				self.log("Data loaded from file: %s (pickle with compresion)"%(fnameCPkl),"purple",0)
		#---- Pickle without compresion
		elif os.path.exists(fnamePkl): 
			fileexists = True
			if not self.isDataReader: self.log("Warning! FEB with ID: %s was already measured."%(self.userID),"orange",0)
			with open(fnamePkl, 'rb') as outfile:
				data = pickle.load(outfile)
				self.measData=data["measData"]
				self.fittedData=data["fittedData"]
				self.log("Data loaded from file: %s (pickle without compresion)"%(fnamePkl),"purple",0)
		#---- JSON format
		elif os.path.exists(fnameJson): 
			fileexists = True
			if not self.isDataReader: self.log("Warning! FEB with ID: %s was already measured."%(self.userID),"orange",0)
			with open(fnameJson, 'r+') as outfile:
				data = json.load(outfile)
				self.measData={}
				for meas in data["measData"]:
					self.measData[meas]={}
					for ch in data["measData"][meas]:
						if ch == "info": self.measData[meas][ch]= data["measData"][meas][ch]
						else: self.measData[meas][int(ch)]= data["measData"][meas][ch]
				self.fittedData={}
				for meas in data["fittedData"]:
					self.fittedData[meas]={}
					for ch in data["fittedData"][meas]:
						self.fittedData[meas][int(ch)]= data["fittedData"][meas][ch]
				self.log("Data loaded from file: %s (json format)"%(fnameJson),"purple",0)
		else:
			if self.isDataReader: self.log("Missing measurements data for FEB with ID: %s!"%(self.userID),"red",0)
			
		#Show information about old measurements if datafile exiists
		if fileexists:
			self.log("Data already measured for FEB (found in its output directory): %s"%(self.userID),"brown",0)
			self.log("Measurements: %s"%( str(list(self.measData.keys())) ),"green",1)
			self.log("Fitted Data: %s"%( str(list(self.fittedData.keys())) ),"green",1)
	
				
	#save data to JSON file
	def saveData(self):
		#---- JSON format
		#fname="%s.json"%(os.path.join(ResultsPath,self.userID))
		#with open(fname, 'w') as outfile:
		#		data = {"measData":self.measData,"fittedData":self.fittedData}
		#		json.dump(data, outfile)
		
		#---- Pickle without compresion
		#fname="%s.dat"%(os.path.join(ResultsPath,self.userID))
		#with open(fname, 'wb') as outfile:
		#		data = {"measData":self.measData,"fittedData":self.fittedData}
		#		pickle.dump(data, outfile)
				
		#---- Pickle with compresion
		fname="%s.cdat"%(os.path.join(ResultsPath,self.userID))
		with bz2.BZ2File(fname, 'w') as outfile: 
				data = {"measData":self.measData,"fittedData":self.fittedData}
				cPickle.dump(data, outfile)


	
	#Function append html line with styled text to logfile
	def log(self,txt,color,indent,printconsole=True):
		fname = os.path.join(ReportsPath,self.userID,"measurements_log.html")
		if printconsole: printc("[%s] %s"%(self.userID,txt),color,indent)
		if not self.isDataReader: #log file is updated only when FEB is initialized for measurements
			with open(fname, 'a') as outfile:
				outfile.write("<span style=\"color:%s;margin-left:%dpx;\">%s<br></span>\n"%(color,20*indent,txt.replace("\n","<br>")))
			
	#--------------- ----------------------
	#        set functions
	#--------------------------------------
	#def setPreamp(self,gain,ptime,verify=False):
		#pasttrec_ctrl.init_board(str(self.fpgaAddr),1,ptime ,gain,5)

	#Function sets gain and peak time of preamp, if verify is set the data is reading back and check
	def setPreamp(self,gain,ptime,verify=False):
		Vref = 1  #1 - internal bandgap, 0 - external pad
		gains={0:"4mV/fC", 1:"2mV/fC", 2:"1mV/fC", 3:"0.67mV/fC"}
		ptimes={0:"10ns", 1:"15ns", 2:"20ns", 3:"35ns"}
		if gain in gains.keys() and ptime in ptimes.keys():
			val = Vref*16 + gain*4 + ptime
			for asic in self.activeAsics: self.writeReg(asic,self.aRegs["PRE"].addr,val)
			self.log("Setting: %s - gain: %d (%s), peaking time: %d (%s)"%(self.aRegs["PRE"].descr,gain,gains[gain],ptime,ptimes[ptime]),"purple",0)
			if verify:
				rvals=self.getPreamp()
				#check both asics or only one if systems knows that only one asic is active
				if (len(self.activeAsics)==2 and rvals[0]==val and rvals[1]==val) or (len(self.activeAsics)==1 and rvals[self.activeAsics[0]]==val):
					rptime = rvals[self.activeAsics[0]]%4
					rgain = int(rvals[self.activeAsics[0]]/4)%4
					self.log("Verified: %s - gain: %d (%s), peaking time: %d (%s)"%(self.aRegs["PRE"].descr,rgain,gains[rgain],rptime,ptimes[rptime]),"green",0)
				else:
					self.log("Error during writing %s"%(self.aRegs["PRE"].descr),"red",0)
					return False
			return True
		else:
			self.log("Values outside range. Gain and peaking time should be in range 0-3!","red",0)
			return False


	#Function sets time cancelation 1 RC values, if verify is set the data is reading back and check
	def setTailCancel1(self,cVal,rVal,verify=False):
		cvs={0:"6.0pF", 1:"7.5pF", 2:"9.0pF", 3:"10.5pF", 4:"12.0pF", 5:"13.5pF", 6:"15.0pF", 7:"16.5pF"}
		rvs={0:"3k", 1:"7k", 2:"11k", 3:"15k", 4:"19k", 5:"23k", 6:"27k", 7:"31k"}
		if cVal in cvs.keys() and rVal in rvs.keys():
			val = cVal*8 + rVal
			for asic in self.activeAsics: self.writeReg(asic,self.aRegs["TC1"].addr,val)
			self.log("Setting: %s - C: %d (%s), R: %d (%s)"%(self.aRegs["TC1"].descr,cVal,cvs[cVal],rVal,rvs[rVal]),"purple",0)
			if verify:
				rvals=self.getTailCancel1()
				if (len(self.activeAsics)==2 and rvals[0]==val and rvals[1]==val) or (len(self.activeAsics)==1 and rvals[self.activeAsics[0]]==val):
					rrVal = rvals[self.activeAsics[0]]%8
					rcVal = int(rvals[self.activeAsics[0]]/8)%8
					self.log("Verified: %s - C: %d (%s), R: %d (%s)"%(self.aRegs["TC1"].descr,rcVal,cvs[rcVal],rrVal,rvs[rrVal]),"green",0)
				else:
					self.log("Error during writing %s"%(self.aRegs["TC1"].descr),"red",0)
					return False
			return True
		else:
			self.log("Values outside range. C and R values should be in range 0-7!","red",0)
			return False


	#Function sets time cancelation 2 RC values, if verify is set the data is reading back and check
	def setTailCancel2(self,cVal,rVal,verify=False):
		cvs={0:"0.60pF", 1:"0.75pF", 2:"0.90pF", 3:"1.05pF", 4:"1.20pF", 5:"1.35pF", 6:"1.50pF", 7:"1.65pF"}
		rvs={0:"5k", 1:"8k", 2:"11k", 3:"14k", 4:"17k", 5:"20k", 6:"23k", 7:"26k"}
		if cVal in cvs.keys() and rVal in rvs.keys():
			val = cVal*8 + rVal
			for asic in self.activeAsics: self.writeReg(asic,self.aRegs["TC2"].addr,val)
			self.log("Setting: %s - C: %d (%s), R: %d (%s)"%(self.aRegs["TC2"].descr,cVal,cvs[cVal],rVal,rvs[rVal]),"purple",0)
			if verify:
				rvals=self.getTailCancel2()
				if (len(self.activeAsics)==2 and rvals[0]==val and rvals[1]==val) or (len(self.activeAsics)==1 and rvals[self.activeAsics[0]]==val):
					rrVal = rvals[self.activeAsics[0]]%8
					rcVal = int(rvals[self.activeAsics[0]]/8)%8
					self.log("Verified: %s - C: %d (%s), R: %d (%s)"%(self.aRegs["TC2"].descr,rcVal,cvs[rcVal],rrVal,rvs[rrVal]),"green",0)
				else:
					self.log("Error during writing %s"%(self.aRegs["TC2"].descr),"red",0)
					return False
			return True
		else:
			self.log("Values outside range. C and R values should be in range 0-7!","red",0)
			return False


	#Function sets LVDS current, if verify is set the data is reading back and check
	def setLvdsCurr(self,curr,verify=False):
		if curr>=0 and curr<8:
			for asic in self.activeAsics: self.writeReg(asic,self.aRegs["LVDS"].addr,curr)
			self.log("Setting: %s - Current: %d"%(self.aRegs["LVDS"].descr,curr),"purple",0)
			if verify:
				rvals=self.getLvdsCurr()
				if (len(self.activeAsics)==2 and rvals[0]==curr and rvals[1]==curr) or (len(self.activeAsics)==1 and rvals[self.activeAsics[0]]==curr):
					self.log("Verified: %s - Current: %d"%(self.aRegs["LVDS"].descr,curr),"green",0)
				else:
					self.log("Error during writing %s"%(self.aRegs["LVDS"].descr),"red",0)
					return False
			return True
		else:
			self.log("Values outside range. Current value should be in range 0-7!","red",0)
			return False


	#Function sets thresholds, if verify is set the data is reading back and check
	def setThreshold(self,thVal,verify=False):
		pasttrec_ctrl.set_threshold_for_board(str(self.fpgaAddr),1,thVal)
	'''
	def setThreshold(self,thVal,verify=False):
		thVs=[-1,-1]
		if type(thVal).__name__=="int": thVs=[thVal,thVal]
		if type(thVal).__name__=="list": thVs=thVal
		if thVs[0]>=0 and thVs[0]<128 and thVs[1]>=0 and thVs[1]<128:
			for asic in self.activeAsics: self.writeReg(asic,self.aRegs["VTH"].addr,thVs[asic])
			self.log("Setting: %s - Threshold ASIC0: %d, Threshold ASIC1: %d"%(self.aRegs["VTH"].descr,thVs[0],thVs[1]),"purple",0,False)
			if verify:
				rvals=self.getThreshold()
				if (len(self.activeAsics)==2 and rvals[0]==thVs[0] and rvals[1]==thVs[1]) or (len(self.activeAsics)==1 and rvals[self.activeAsics[0]]==thVs[self.activeAsics[0]]):
					self.log("Verified: %s - Threshold ASIC0: %d, Threshold ASIC1: %d"%(self.aRegs["VTH"].descr,thVs[0],thVs[1]),"green",0)
				else:
					self.log("Error during writing %s"%(self.aRegs["VTH"].descr),"red",0)
					return False
			return True
		else:
			self.log("Values outside range. Threshold value should be in range 0-127!","red",0)
			return False
'''

	#Function sets baselines for all channels in FEB, if verify is set the data is reading back and check
	def setBaselines(self, baseVals,verify=False):
		if len(baseVals)==16:
			ok=True
			brmin=0
			brmax=16
			if len(self.activeAsics)==1: 
				brmin=8*self.activeAsics[0]
				brmax=8*self.activeAsics[0]+8
			for ch in range(16):
				if ch<brmin or ch>=brmax: continue
				if baseVals[ch]>=0 and baseVals[ch]<32:
					self.writeReg(int(ch/8),self.aRegs["BASE%d"%(ch%8)].addr,baseVals[ch])
					#printc("Setting: %s ASIC%d - Value %d"%(self.aRegs["BASE%d"%(ch%8)].descr,int(ch/8),baseVals[ch]),"purple",0)
				else:
					self.log("Values outside range. Baseline value should be in range 0-31!","red",0)
					ok=False
			if ok:
				self.log("Setting baselines: %s"%(str(baseVals)),"purple",0,False)
			if verify:
				rvals=self.getBaselines()
				if rvals[brmin:brmax]==baseVals[brmin:brmax]:
					self.log("Verified: Baseline trim registers - All baselines successfully written","green",0)
				else:
					self.log("Error during writing Baseline trim registers","red",0)
					print("Write: ",baseVals[brmin:brmax])
					print("Read:  ",rvals[brmin:brmax])
					ok=False
			return ok
		else:
			self.log("Baseline table has wrong size (%d values) 16 values needed for one FEB!"%(len(baseVals)),"red",0)
			return False


	#--------------- ----------------------
	#        get functions
	#--------------------------------------

	#reading preamp configuration for both asics in FEB, when asic is not specified returns list of 2 values
	def getPreamp(self,asic=None):
		return self.getRegByID("PRE",asic)


	#reading TC1 configuration for both asics in FEB, when asic is not specified returns list of 2 values
	def getTailCancel1(self,asic=None):
		return self.getRegByID("TC1",asic)


	#reading TC2 configuration for both asics in FEB, when asic is not specified returns list of 2 values
	def getTailCancel2(self,asic=None):
		return self.getRegByID("TC2",asic)


	#reading LVDS current for both asics in FEB, when asic is not specified returns list of 2 values
	def getLvdsCurr(self,asic=None):
		return self.getRegByID("LVDS",asic)


	#reading threshold for both asics in FEB, when asic is not specified returns list of 2 values
	def getThreshold(self,asic=None):
		return self.getRegByID("VTH",asic)


	#reading baselins for 16 channels on the FEB (both asics)
	def getBaselines(self):
		baseVals=[]
		for ch in range(16):
			baseVals.append(self.readReg(int(ch/8),self.aRegs["BASE%d"%(ch%8)].addr))
		return baseVals

	#--------------- ----------------------
	#        tssts and presets
	#--------------------------------------
	
	#Functions sets FEB in one of typical configurations 
	def setTypicalConfiguration(self, confName):
		presets={}
		#----------------------------------------------------
		presets["1mV20ns"]={"gain":2, "ptime":2, "c1":0, "r1":5, "c2":0, "r2":2} #K = 1mV/fC, peakT = 20ns
		presets["2mV15ns"]={"gain":1, "ptime":1, "c1":6, "r1":1, "c2":0, "r2":1} #K = 2mV/fC, peakT = 15ns
		presets["2mV20ns"]={"gain":1, "ptime":2, "c1":1, "r1":6, "c2":1, "r2":4} #K = 2mV/fC, peakT = 20ns
		presets["4mV15ns"]={"gain":0, "ptime":1, "c1":5, "r1":4, "c2":6, "r2":6} #K = 4mV/fC, peakT = 15ns
		presets["4mV20ns"]={"gain":0, "ptime":2, "c1":3, "r1":6, "c2":2, "r2":5} #K = 4mV/fC, peakT = 20ns
		#----------------------------------------------------
		if confName in presets.keys():
			tc=presets[confName]
			ok = True
			ok &= self.setPreamp(tc["gain"],tc["ptime"],True)
			ok &= self.setTailCancel1(tc["c1"],tc["r1"],True)
			ok &= self.setTailCancel2(tc["c2"],tc["r2"],True)
			#ok &=self.setThreshold(tc["th"],True)
			if ok:
				self.log("FEB is now in typical configuration: %s"%confName,"green",0)
			else:
				self.log("There were some errors during setting configuration: %s"%confName,"red",0)
		else:
			self.log("Typical configuration: %s is not known!"%confName,"red",0)
			self.log("Select one of: %s"%(", ".join(presets.keys())),"green",0)
	

	#Function test all registers on FEB board, returns True if everything is ok
	def testAllRegisters(self):
		regsToTest=["PRE","TC1","TC2","VTH","BASE0","BASE1","BASE2","BASE3","BASE4","BASE5","BASE6","BASE7","LVDS"]
		self.log("Starting test registers procedure ... (FPGA:%d, CABLE:%d)"%(self.fpga,self.cable),"blue",0)
		self.activeAsics = [0]
		for regid in regsToTest:
			reg = self.aRegs[regid]
			vals = reg.testVals + [reg.defVal] #all test values + default in the end
			self.log("Testing: %s ..."%(reg.descr),"purple",0)
			remIdx=[]
			for asic in self.activeAsics:
				rvals=[]
				for val in vals:
					self.writeReg(asic,reg.addr,val)
					#time.sleep(0.05)
					rvals.append(self.readReg(asic,reg.addr))
				if vals == rvals: 
					self.log("Asic:%d \tWriting: %s ... \tReading: %s ... \tOK"%(asic,hexl(vals),hexl(rvals)),"green",1)
				else:
					remIdx.append(asic)
					self.log("Asic:%d \tWriting: %s ... \t Reading: %s ... \tError"%(asic,hexl(vals),hexl(rvals)),"red",1)
			for i in remIdx: self.activeAsics.remove(i)
			if len(self.activeAsics)==0: break
		#print()
		
		self.measData["FebInfo"]["activeAsics"] = self.activeAsics
		self.activeChannels = list(range(8*self.activeAsics[0],8*self.activeAsics[0]+8)) if len(self.activeAsics)==1 else list(range(0,16))
		self.measData["FebInfo"]["activeChannels"] = self.activeChannels
		
		if len(self.activeAsics) == 2: self.log("FEB:%s (FPGA:%d, CABLE:%d). All registers in both asics successfully tested."%(self.userID,self.fpga,self.cable),"green",0)
		elif len(self.activeAsics) == 1: self.log("FEB:%s (FPGA:%d, CABLE:%d). All registers (in ASIC:%d only) successfully tested."%(self.userID,self.fpga,self.cable,self.activeAsics[0]),"orange",0)
		else: self.log("FEB:%s (FPGA:%d, CABLE:%d). There was some errors during write/read operations!"%(self.userID,self.fpga,self.cable),"red",0)
		return len(self.activeAsics)>0
		
	
	#Function reads asic configuration and return it as dictionary
	#Configuration is read only from first active asic (except baselines) assuming that both asics are in the same settings
	def getFullConfiguration(self):
		ret={}
		self.activeAsics = [0]
		gpt = self.getPreamp(self.activeAsics[0])
		ret["gain"] = int((gpt/4))%4
		ret["ptime"] = gpt%4
		ret["tc1"] = self.getTailCancel1(self.activeAsics[0])
		ret["tc2"] = self.getTailCancel2(self.activeAsics[0])
		ret["vth"] = self.getThreshold(self.activeAsics[0])
		ret["base"] = self.getBaselines()
		return ret
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
	
if __name__=="__main__":
	
	#pandaFeb = PANDAfeb(0,"B001",True)
	pandaFeb = PANDAfeb(1,"B002",True)
	#pandaFeb = PANDAfeb(2,"B003",True)
	#pandaFeb = PANDAfeb(3,"B004",True)
	
	#print(pandaFeb.testAllRegisters())
	
	#pandaFeb.setTypicalConfiguration("k1_tp2_v1")
	#print()
	#pandaFeb.setTypicalConfiguration("ble")
	
	#printdict(pandaFeb.aRegs)

	#pandaFeb.writeReg(0,0x00300,0x0A)
	#pandaFeb.writeReg(1,0x00300,13)
	
	#print(pandaFeb.readReg(0,0x00300))
	#print(pandaFeb.readReg(1,0x00300))             
  
	'''
	print(pandaFeb.setPreamp(2,2))
	print("-----")
	print(pandaFeb.setPreamp(2,1,True))
	
	print(pandaFeb.setTailCancel1(2,1,True))
	print(pandaFeb.setTailCancel1(2,1,True))
	print(pandaFeb.setLvdsCurr(6,True))
	print(pandaFeb.setThreshold([32,33],True))
	print(pandaFeb.setThreshold(16,True))
	
	
	
	basetab=[13,14,15,14,12,9,20,12,15,15,16,17,13,14,15,14]
	print(pandaFeb.setBaselines(basetab,True))
	
	
	basetab=[13,14,15,14,12,9,20,12,15,15,16,17,13,14,15,12]
	print(pandaFeb.setBaselines(basetab,True))
	
	print(basetab)
	print("-----")
	print(pandaFeb.getBaselines())
  
  
	pandaFeb.setTypicalConfiguration("tp1")

	print("TC1: ",pandaFeb.getPreamp())
	print("TC1: ",pandaFeb.getTailCancel1())
	print("TC2: ",pandaFeb.getTailCancel2())  
	print("VTH: ",pandaFeb.getThreshold()) 
	print("LVDS: ",pandaFeb.getLvdsCurr()) 
  
  '''
	#print(pandaFeb.getFullConfiguration())
