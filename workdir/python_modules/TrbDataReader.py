#!/usr/bin/env python3
import os
import time
import sys, tty, termios
import subprocess
from statistics import stdev, mean

from config import *

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class TrbDataReader:
	#--------------- ----------------------
	#        Consts
	#--------------------------------------
	c_fpga = [0xc001]
	def_scalers_reg = 0xdfc0
	def_pastrec_channels_all = 48  #3x FEB on one cable
	#--------------- ----------------------
	#        INIT and general functions and private
	#--------------------------------------
	def __init__(self,testBranches=list(range(9))):
		self.testBranches = testBranches
		print("Branches: ",self.testBranches)
	
	
	#Function run trb command and return its string output
	def readScalers(self,address):
		l = [ 'trbcmd', 'rm', hex(address), hex(self.def_scalers_reg), hex(self.def_pastrec_channels_all), '0' ]
		rc = subprocess.run(l, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		return rc.stdout.decode()
	
	
	#Function parse string data from trb read memory command and returns list of 48 ints (3xFEB)
	#Address as optional argument can be set for test purposes  
	def parseScalers(self,res,address=None):
		ret = [0] * self.def_pastrec_channels_all
		for l in res.splitlines():
			if "H: " in l:
				if address is not None and int(l.split()[1],16) != address:
					printc("Address in data header (%s) is different than expected (%s)!"%(hex(int(l.split()[1],16)),hex(address)),"err",0)
					break
			else:
				ll = l.split()
				if len(ll) == 2:
					chn = int(ll[0], 16) - self.def_scalers_reg
					if chn > self.def_pastrec_channels_all:
							printc("Channel number (%d) is outside range!"%(chn),"err",0)
							continue
					val = int(ll[1], 16)
					if val >= 0x80000000: val -= 0x80000000
					ret[chn] = val
		return ret
	
	
	#Function calculate counts diff
	def countsDiff(self,t2,t1):
		ret=[]
		if len(t2) == len(t1):
			for i in range(len(t2)):
				val = t2[i] - t1[i]
				if val < 0: val += 0x80000000
				ret.append(val)
		return ret
	
	
	#Function allow to start and stop trigger for TOT measurements
	def setTriggerEnabled(self, state):
		if state:
			#os.system("trbcmd w 0x8000 0xa101 0xffff0001") # trg_channel_mask: edge=1111 1111 1111 1111, mask=0000 0000 0000 0001
			#enabel trigger (pulser0)
			os.system("trbcmd w 0xc001 0xa101 0xffff0002")	
			# set pulser to trigger CTS data taking to 1 kHz
			os.system("trbcmd w 0xc001 0xa13b 0x0001869f")
			time.sleep(1.0)
		else:
			#os.system("trbcmd w 0x8000 0xa101 0xffff0000")  # trg_channel_mask: edge=1111 1111 1111 1111, mask=0000 0000 0000 0000
			#disabel trigger (pulser0)
			os.system("trbcmd w 0xc001 0xa101 0xffff0000")	
			
	
	#Function run hldprint command and parse its string output, prec argument = precision in ns
	def readToT(self, prec=0.5):
		retToT={}
		for i in range(1):
			l = [ 'hldprint', 'localhost:6789', '-tdc', '0x1000', '-num', '5']
			rc = subprocess.run(l, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			chanToT={}
			chanOffset=-1
			for line in rc.stdout.decode().splitlines():
				#if "id 0xc167 full" in line:
					#chanOffset=-1
					#continue
				#if "id 0x5555 full" in line:
					#chanOffset=47
					#continue
				if "hit  ch:" in line and "tot:" in line:
					ch = int(line.split("hit  ch:")[1].strip(" ").split(" ")[0].strip(" \t\n"))+chanOffset
					tot = float(line.split("ns tot:")[1].strip(" ").split(" ")[0].strip(" \t\n").replace("\x1b[31m","").replace("\x1b[32m",""))
					#try:
					#	tot = float(line.split("ns tot:")[1].strip(" ").split(" ")[0].strip(" \t\n").replace("\x1b[31m","").replace("\x1b[32m",""))
					#except:
					#	continue
					#if ch > 7:  continue
					if tot < 30: continue ## spike rejection
					if tot > 10000: continue
					#print("channel ", ch , "ToT: ",tot) 
					#printc("ToT: %d\n","blue",tot)
					if not ch in chanToT.keys():
						chanToT[ch]=[tot]
					else:
						chanToT[ch].append(tot)

			retToT={}
			stdevs=[0.0]
			for ch in chanToT:
				totList=sorted(chanToT[ch])
				if ch < 128 and len(totList)>12:
					totList=totList[5:-5]
					#print (totList);
					ave = mean(totList)
					std = stdev(totList)
					stdevs.append(std)
					#print(ch,totList,len(totList)," - ",ave,std)
					retToT[ch] = ave
					#print("totmean",ave)
			#print("STDev all channels: ",stdevs)
			
			if max(stdevs)<prec: break
			
			printc("TOT stdev: %0.3f [ns] is too big (>%0.2f ns)... Measure once again!"%(max(stdevs),prec),"err",0)
			time.sleep(0.1)
			
		return (retToT, max(stdevs))
	
	
	#--------------- ----------------------
	#       Functions
	#--------------------------------------
	
	#Function returns counts colected in measTime for all branches
	#Returns dictionary ret[branch]=[16 ints for one feb]
	def getCounts(self,measTime=0.5):
		trbDta1={}  #data structure trbDta[trb=0,1,2]="string output" or 48 ints after parsing
		trbDta2={}
		for br in self.testBranches:
			if not int(br/3) in trbDta1.keys(): trbDta1[int(br/3)]=""
			if not int(br/3) in trbDta2.keys(): trbDta2[int(br/3)]=""
		
		#reading first count value of all selected test branches
		for trb in trbDta1.keys(): 
			trbDta1[trb]=self.readScalers(self.c_fpga[trb])
		#waiting....
		time.sleep(measTime)
		#reading second count value of all selected test branches
		for trb in trbDta2.keys():
			trbDta2[trb]=self.readScalers(self.c_fpga[trb])
		#parsing data...
		for trb in trbDta1.keys():
			trbDta1[trb]=self.parseScalers(trbDta1[trb],self.c_fpga[trb])
			trbDta2[trb]=self.parseScalers(trbDta2[trb],self.c_fpga[trb])
		
		ret={}
		for br in self.testBranches:
			trb=int(br/3)  #select proper trb (fpga)
			n = (br%3)*16  #data index - where 16 channel data is started
			diff = self.countsDiff(  trbDta2[trb][n:n+16] , trbDta1[trb][n:n+16]  )
			ret[br] = diff
		return ret
		

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
	
if __name__=="__main__":
	
	print("Reading counts...")
	
	trbR = TrbDataReader()
	
	'''
	print("\n"*(len(trbR.testBranches)+2))
	while(1):
		counts = trbR.getCounts()
		clear_n_lines(len(trbR.testBranches)+2)
		printdict(counts)
	'''               
	
	trbR.setTriggerEnabled(True)
	
	printdict(trbR.readToT())

	trbR.setTriggerEnabled(False)










