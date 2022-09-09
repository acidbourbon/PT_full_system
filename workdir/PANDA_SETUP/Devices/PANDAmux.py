#!/usr/bin/env python3
import serial, os
import time
import sys, tty, termios

#import glob
import math

from config import *

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------

class PANDAmux():
	#--------------- ----------------------
	#        COMMANDS Const
	#--------------------------------------
	Const_test_ping = 0

	Const_set_chn_number = 1
	Const_set_chn_mask = 2
	Const_set_indicator = 3
	
	Const_set_qin_factors = [*range(16,32)]
	Const_get_qin_factors = [*range(80,96)]
	
	Const_get_active_chns = 64
	Const_get_hwd_addr = 125
	#--------------- ----------------------
	#        INIT and general functions
	#--------------------------------------
	def __init__(self,serport):
		self.serport = serport
		self.ser = serial.Serial(self.serport, 19200, timeout=0.5, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
		self.hwdaddr=1000 #some fake address
		self.qinFactors=16*[1.0]
		if self.ping():
			self.hwdaddr = self.getHwdAddress()
			self.qinFactors = self.getQinFactors()
			printc("PANDA charge injector on port %s is connected ...\t Hardware address: %02d"%(self.serport,self.hwdaddr),"green",0)
		else: 
			printc("Device on port %s is not responding as PANDA charge injector!"%self.serport,"err",0)
		

	def closeConnection(self):
		self.ser.close()
	
	#return bit value at selected position 
	def getBitVal(self,val,bitnr):
		return (val/int(math.pow(2,bitnr)))%2

	#write command via uart and return read data or error
	#cfg_bytes: command, val_MSB, val_LSB
	#returned value: ["err",vals.... , ...]
	def write_read_uart(self,cfg_bytes):
		writeloop=True
		runs=0
		while writeloop:
			runs+=1
			head=128
			data=""
			#code msb of bytes in header to avoid sending values >128 except header
			for i in range(len(cfg_bytes)): 
				val=cfg_bytes[i]
				if val>=128:
					val-=128
					head+=int(math.pow(2,i))
				data+=chr(val)
			data=chr(head)+data
			self.ser.write(data.encode())
			#try to read 6 bytes 
			err=["err"]
			fifo=self.ser.read(6)
			if len(fifo)>=6:
				if fifo[0]==fifo[3] and fifo[1]==fifo[4] and fifo[2]==fifo[5]: 
					if cfg_bytes[0]<64 or cfg_bytes[0]>=128:        #only for Set command and chip commands which sends ping as ack
						if fifo[1]==cfg_bytes[1] and fifo[2]==cfg_bytes[2]:
							writeloop=False
							return ["ok",fifo[1],fifo[2]]
						else:
							err.append("Data ping error")
					else:
						writeloop=False
						#print(["ok",fifo[1],fifo[2]])
						return ["ok",fifo[1],fifo[2]]
				else: err.append("Data corrupted")
			else: err.append("Data length %d, expected: 6 bytes"%len(fifo))
			#try only 3 times
			if runs==3: return err
			
	#--------------- ----------------------
	#        Main
	#--------------------------------------
	
	#sends ping command to the injection board
	def ping(self):
		out = self.write_read_uart([self.Const_test_ping,0,1])
		if out[0] == "ok":
			return True
		else: 
			#print("ERROR: ",out)
			return False
	
	
	#read the hardware address selected on the injesctor board by 4 jumpers
	#returns value 0-15
	def getHwdAddress(self):
		out=self.write_read_uart([self.Const_get_hwd_addr,0,0])
		if out[0]!="ok": 
			print("[%02d]ERROR(getHwdAddress): "%self.hwdaddr,out)
			return 1000
		else: return out[1]
	
	#--------------- ----------------------
	#        Set parameter
	#--------------------------------------
	
	#set only one active channel 0-7, numbers greather than 7 switch off all channels
	def setActiveChannel(self,chn):
		if chn == None: chn = 10 #switch off all channels
		val = chn%256
		#print(val)
		out=self.write_read_uart([self.Const_set_chn_number,val,val])
		if out[0] != "ok": print("[%02d]ERROR (setActiveChannel): "%self.hwdaddr,out)
	
	
	#set Active channel mask switch on inputs according to 8-bit mask. MSB = chn7, ..., LSB = chn0
	#example: mask = 3 (bin: 00000011) -> channels 0 and 1 are active
	def setActiveChannelMask(self,mask):
		val = mask%256
		out=self.write_read_uart([self.Const_set_chn_mask,val,val])
		if out[0] != "ok": print("[%02d]ERROR (setActiveChannelMask): "%self.hwdaddr,out)
	
	
	#set LED Indicators connected to the ISP
	#examples: stat = None -> all LEDs off, stat = "ok" or True -> green LED, stat = "err" or False -> red LED, stat = 7 -> All LEDs ON
	def setIndicator(self,stat):
		val=0
		if stat == None: val = 0 #switch off all LEDs
		if type( stat ) is str:
			if stat.lower() == "ok": val = 1
			if stat.lower() == "err": val = 2
			if stat.lower() == "warn": val = 3
		if type( stat ) is bool:
			if stat : val = 1
			else: val = 2
		if type( stat ) is int:
			val = stat%8
		#print(val)
		out=self.write_read_uart([self.Const_set_indicator,val,val])
		if out[0] != "ok": print("[%02d]ERROR (setIndicator): "%self.hwdaddr,out)


	#write qin Factors given as list of 16 floats(range 0.673 - 1.327)
	#function sets also a class variable self.qinFactors if operation was fully successful
	#forceWrite can be used to skip confirmation question
	def setQinFactors(self,factors,forceWrite=False):
		hrangeFull = 0.32768  #half range: 65536/100000/2 
		hrange = int(hrangeFull*1000.0)/1000.0  #trimmed value - no rounding
		if len(factors)==16:
			IsOK=True
			printc("Writing calibration factors to Jnjector's EEPROM (at address: %d) ..."%(self.hwdaddr),"blue",0)
			for fac in factors:
				if fac >= 1.0+hrange or fac <= 1.0-hrange: IsOK = False
			if IsOK:
				print(factors)
				IsOK = forceWrite
				if not IsOK: 
					printc("Do you really want to write all factors to EEPROM (type \"yes\" to confirm):","warn",0)
					IsOK = input().lower() == 'yes'
				if IsOK:
					#printc("All factors will be stored with precision: %0.8f"%(1.0/65536.0),"blue",0)
					for i in range(16):
						wval = int(round((factors[i]-1.0+hrangeFull) * 100000.0,0))
						rounddedval=float(wval)/100000.0+1.0-hrangeFull  
						printc("Factor %02d: Value: %0.10f will be stored as: %0.5f (%d)"%(i,factors[i],rounddedval,wval),"purple",0)
						#---------- Writing EEPROM
						out=self.write_read_uart([self.Const_set_qin_factors[i],int(wval/256),int(wval%256)])
						if out[0] != "ok": print("[%02d]ERROR (setQinFactors): "%self.hwdaddr,out)
						#---------- Reading EEPROM back
						out=self.write_read_uart([self.Const_get_qin_factors[i],0,0])
						if out[0]!="ok": 
							print("[%02d]ERROR (getQinFactors): "%self.hwdaddr,out)
						else: 
							rval = out[1]*256+out[2]
						if wval!=rval:
							printc("Writed value %d are different than %d read from EEPROM!"%(wval,rval),"err",0)
							IsOK = False
					if IsOK:
						printc("Operation successfully completed! Reading factors back...","blue",0)
						self.qinFactors = self.getQinFactors()
						print(self.qinFactors)
					else:
						printc("Something gone wrong... check connections and factor values!","err",0)
			else:
				printc("All factors should be in range: %0.5f - %0.5f! Check values below:"%(1.0-hrange,1.0+hrange),"err",0)
				print(factors)
		else:
			printc("Factors list should contain 16 float values, not %d!"%len(factors),"err",0)
		

	#--------------- ----------------------
	#        Get parametres
	#--------------------------------------

	#read the active channels as 8-bit value. MSB = chn7, ..., LSB = chn0
	#exmaple: returned value = 5 -> channels 0 and 2 are active 
	def getActiveChannels(self):
		out=self.write_read_uart([self.Const_get_active_chns,0,0])
		if out[0]!="ok": 
			print("[%02d]ERROR (getActiveChannels): "%self.hwdaddr,out)
			return 1000
		else: return out[1]


	#read qin factors from injector's EEPROM, returns list of 16 float numbers
	#if something is wrong value 1.0 is returned as default factor value
	def getQinFactors(self):
		hrangeFull = 0.32768  #half range: 65536/100000/2 
		factors=[]
		for i in range(16):
			out=self.write_read_uart([self.Const_get_qin_factors[i],0,0])
			if out[0]!="ok": 
				print("[%02d]ERROR (getQinFactors): "%self.hwdaddr,out)
				factors.append(1.0)
			else: 
				rval = out[1]*256+out[2]
				fval=round(float(rval)/100000.0+1.0-hrangeFull,5)
				if rval < 60 or rval >65500:
					if rval == 0:
						printc("Factor %02d, value %0.5f (%d): Data in EEPROM corrupted!"%(i,fval,rval),"err",0)
					elif rval == 65535:
						printc("Factor %02d, value %0.5f (%d): No data in EEPROM!"%(i,fval,rval),"err",0)
					else:
						printc("Factor %02d, value %0.5f (%d): Value outside range!"%(i,fval,rval),"err",0)
					fval = 1.0
				factors.append(fval)
		return factors







#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------

class PANDAinjectors():
	Cinj = 10.0*10**(-12) #[F]
	
	#globConvFactor is calculated from components placed on the board and delta splitter resistance
	#For better understanding see injector_conn_calc.pdf in documentation directory
	#R = {"Rg":50.0, "Rd":50.0,  "Ra":47.0, "Rs":1800.0, "R1":75.0, "R2":24.0} #[Ohm]
	#R = {"Rg":50.0, "Rd":50.0,  "Ra":47.0, "Rs":2400.0, "R1":150.0, "R2":47.0} #[Ohm] old injector
	R = {"Rg":50.0, "Rd":0.0,  "Ra":47.0, "Rs":1800.0, "R1":75.0, "R2":24.0} #[Ohm] Frankfurt version

	Rz1 = (R["R1"] + R["R2"]) / 2.0
	Rz2 = R["Ra"] * Rz1 / (R["Ra"] + Rz1)
	Rz3 = R["Ra"] * (R["Rs"] + Rz2) / (R["Ra"] + R["Rs"] + Rz2)
	Rz4 = (R["Rd"]/3.0 + Rz3) / 2.0
	#print(Rz1, Rz2, Rz3, Rz4)
	
	Xgg = 2.0 * Rz4 / (R["Rg"] + R["Rd"]/3.0 + Rz4) #Ugg = Ug * Xgg
	Xa = Rz3 / (R["Rd"]/3.0 + Rz3) # Ua = Ugg * Xa
	Xd = Rz2 / (R["Rs"] + Rz2) # Ud = Ua * Xd
	Xcap = R["R2"] / (R["R1"] + R["R2"]) #Ucap = Ud * Xcap
	#print(Xgg, Xa, Xd, Xcap)
	
	#print("Va  : ", 5.0*Xgg*Xa," V")
	#print("Vd  : ", 5.0*Xgg*Xa*Xd*1000.0," mV")
	#print("Vcap: ", 5.0*Xgg*Xa*Xd*Xcap*1000.0," mV")
	#--------------- ----------------------
	#        INIT and general functions
	#--------------------------------------
	def __init__(self,externalDivider=1.0):
		self.InjObjects={}
		self.InjAddresses=[]
		self.globConvFactor=self.Cinj*self.Xgg*self.Xa*self.Xd*self.Xcap/echarge/1000.0 # [ke-/V]
		printc("Searching for devices...","purple",0)
		for serport in getSerialPorts():
			if "mux" in serport:
				inj = PANDAmux(serport)
				if inj.hwdaddr > 15: continue
				if inj.hwdaddr in self.InjObjects.keys(): 
					printc("Device with hardware address %02d already exists! Check configuration."%(inj.hwdaddr),"err",0)
				else:
					self.InjObjects[inj.hwdaddr]=inj
					self.InjAddresses.append(inj.hwdaddr)
		printc("List of PANDA injectors (muxes):","purple",0)
		for inj in self.InjObjects:
			printc("  Address: %02d  Port: %s"%(self.InjObjects[inj].hwdaddr,self.InjObjects[inj].serport),"green",0)
		printc("Global conversion factor (amplitude [V] -> charge [ke-]) is set to: %f [ke-/V]"%(self.globConvFactor),"blue",0)
		
		
	def closeConnection(self, addrlist=[]):
		if addrlist == []: addrlist = self.InjObjects.keys()
		for addr in addrlist:
			if not addr in self.InjObjects.keys():
				printc("Injector with hardware address %02d doesn't exists!"%(addr),"err",0)
				continue
			self.InjObjects[addr].closeConnection()

	#--------------- ----------------------
	#        Set active channels
	#--------------------------------------
	
	def setActiveChannel(self, chn, addrlist=[]):
		if addrlist == []: addrlist = self.InjObjects.keys()
		for addr in addrlist:
			if not addr in self.InjObjects.keys():
				printc("Injector with hardware address %02d doesn't exists!"%(addr),"err",0)
				continue
			self.InjObjects[addr].setActiveChannel(chn)
		
	def setActiveChannelMask(self,mask, addrlist=[]):
		if addrlist == []: addrlist = self.InjObjects.keys()
		for addr in addrlist:
			if not addr in self.InjObjects.keys():
				printc("Injector with hardware address %02d doesn't exists!"%(addr),"err",0)
				continue
			self.InjObjects[addr].setActiveChannelMask(mask)
		
	#--------------- ----------------------
	#        Get parametres
	#--------------------------------------
	
	def getActiveChannels(self):
		ret={}
		for addr in self.InjObjects.keys(): 
			ret[addr]=self.InjObjects[addr].getActiveChannels()
		return ret
	









#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
	
if __name__=="__main__":
	
	
	Injectors = PANDAinjectors()
	
	
	print() 
	printc("Addresses of known injectors:","blue",0)
	print("\t",Injectors.InjAddresses)
	
	print() 
	printc("Testing active channel function...","blue",0)
	for val in [5, 1, 7, 2]:
		printc("Set active channel: %d and read it back:"%val,"green",1)
		Injectors.setActiveChannel(val)
		print("\t",Injectors.getActiveChannels())
		
	print() 
	printc("Reading Qin Factors:","blue",0)
	for addr in sorted(Injectors.InjAddresses):
		printc("Qin Factors for injector %02d:"%addr,"green",1)
		print("\t",Injectors.InjObjects[addr].qinFactors)
		
	print() 
	printc("Checking indicators...","blue",0)
	for i in range(1):
		for addr in Injectors.InjAddresses:
			Injectors.InjObjects[addr].setIndicator("ok")
		time.sleep(1.0)
		for addr in Injectors.InjAddresses:
			Injectors.InjObjects[addr].setIndicator("err")
		time.sleep(1.0)
		for addr in Injectors.InjAddresses:
			Injectors.InjObjects[addr].setIndicator("warn")
		time.sleep(1.0)
		for addr in Injectors.InjAddresses:
			Injectors.InjObjects[addr].setIndicator(None)
		time.sleep(1.0)

		
	#HERE should be the calibration of injector based on one selected board with known parameters.
	#Factors based on manual calibration... for now
	#0 : [1.00476, 1.00089, 1.00048, 1.01392, 0.99240, 1.00260, 0.99401, 0.99410, 1.00499, 0.99596, 0.99272, 1.00524, 1.00372, 0.99929, 0.99954, 0.99586],
	
	factors = {
		0 : [1.00593, 1.00177, 1.00170, 1.01482, 0.99336, 1.00338, 0.99460, 0.99474, 1.00560, 0.99641, 0.99335, 1.00544, 1.00422, 0.99984, 0.99952, 0.99633],
		1 : [1.00516, 0.99585, 0.99800, 1.00888, 1.00371, 1.00474, 0.99857, 0.99985, 1.00686, 0.99889, 0.99071, 1.00160, 0.99689, 0.99665, 1.00366, 0.99819],
		2 : [0.99663, 0.99626, 0.99107, 0.99305, 0.98679, 0.99376, 0.99237, 0.98031, 0.98955, 0.99528, 0.99869, 0.99559, 0.99639, 0.99250, 0.99677, 0.99618],
		3 : [0.99635, 0.99739, 0.99097, 0.99884, 0.98851, 0.99862, 0.99377, 0.99645, 0.99921, 1.00179, 0.99809, 0.99342, 0.99395, 0.98757, 0.99933, 0.99894],
		4 : [1.00780, 1.00358, 0.99580, 1.00837, 1.00014, 1.00397, 1.00569, 0.99614, 1.00684, 1.00230, 0.99463, 1.00520, 1.00000, 1.00936, 0.99359, 0.99500],
		5 : [0.99514, 0.99532, 0.99568, 1.00169, 0.99957, 0.98935, 0.99149, 0.99699, 0.99579, 0.99937, 0.99515, 0.99756, 0.99114, 0.99497, 0.98891, 0.98942],
		6 : [0.99945, 0.99921, 0.99325, 1.00828, 0.99112, 0.98988, 0.98177, 0.99484, 0.98227, 0.99683, 0.99549, 0.98926, 0.98400, 0.99331, 0.98718, 0.98819],
		7 : [0.99288, 0.98982, 0.99313, 0.99080, 0.99197, 0.99606, 0.99154, 0.98951, 0.99057, 0.98823, 0.99348, 0.99126, 0.99661, 0.99049, 0.98982, 0.99201]
		}
	
	'''
	for addr in sorted(Injectors.InjAddresses):
		if addr in factors.keys():
			Injectors.InjObjects[addr].setQinFactors(factors[addr])
		else:
			printc("Missing Qin Factors for injector: %02d"%addr,"red",1)
	
	'''

	
	Injectors.closeConnection()









 
