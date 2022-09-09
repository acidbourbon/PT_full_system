#!/usr/bin/env python3
import serial, os
import time
import glob
import sys, tty, termios

#----------------------------------- prints colored text
def printc(txt,t,indent=0):
	ct={"err":"1;31","warn":"1;33","def":"0;0","blue":"1;34","green":"0;32","purple":"0;35","orange":"33","brown":"0;33","cyan":"0;36","red":"1;31"}
	print("%s\033[%sm%s\033[0m"%("  "*indent,ct[t],txt))

#print dictonaries in more readable format
def printdict(dic,indent=0):
	for key in sorted(dic.keys()):
		if type(dic[key]).__name__ == "dict":
			print("%s\033[0;32m%s\033[0m :"%("   "*indent,key))
			printdict(dic[key],indent+1)
		else:
			print("%s\033[0;32m%s\033[0m : %s :\"\033[0;35m%s\033[0m\""%("   "*indent,key,type(dic[key]).__name__,dic[key]))

#print lists in more readable format
def printlist(lst):
	print("\033[1;34m-----------------------------------------------------------------------------------------------------\033[0m")
	for i in range(len(lst)):
		print("  \033[0;32m%d\033[0m : %s :\"\033[0;35m%s\033[0m\""%(i,type(lst[i]).__name__,lst[i]))
	print("\033[1;34m-----------------------------------------------------------------------------------------------------\033[0m")









#---------------------------------- clear n last printed lines in console
def clear_n_lines(n):
	clr='\033[%dA'%n
	for i in range(n):
		clr+='\033[2K\n'
	clr+='\033[%dA'%(n+1)
	print(clr)

#--------------------------------- return binary representation of value val as string
def binary(val,bits):
		out=""
		while bits>0:
			if val%2==0:
				out="0"+out
			else:
				out="1"+out
			bits-=1
			val/=2
		return out
		
#--------------------------------- convert list of numbers to hex string
def hexl(vals):
	out=""
	for v in vals: out+=hex(v)+", "
	return out.strip(", ")

#---------------------------------- float range - gives table of float values
def frange(start,stop,step):
	ret=[]
	x=start
	while x<=stop:
		ret.append(x)
		x+=step
	return ret
	
#---------------------------------- scan all possible ports in system and return only active rs232 ports
def getSerialPorts():
	if sys.platform.startswith('win'):
		ports = ['COM%s' % (i + 1) for i in range(256)] 
	elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
		ports = glob.glob('/dev/tty[A-Za-z]*')
	else:
		raise EnvironmentError('Unsupported operating system!')
	result = []
	for port in ports: 
		try:
			s = serial.Serial(port)
			s.close()
			result.append(port)
		except (OSError, serial.SerialException):
			pass
	return result


