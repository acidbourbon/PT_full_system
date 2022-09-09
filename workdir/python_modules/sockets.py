#!/usr/bin/env python

"""@package docstring
Sockets to comunicate with devices

More details.
"""

import socket

try:
	import gpib
except:
	class gpib:
		def __init__(self):
			pass
		
		def listener(self,chn,address):
			return False
		
		def dev(self,chn,address):
			return False
	

KNOWN_SOCKETS_TYPES=['ip','gpib','uart']

class socket_ip():
	def __init__(self,ip,port=5025,name=""):
		self.s = None
		try :
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.s.connect((ip,port))
		except:
			self.s = None
			print("ERROR: IP connection error")
			raise

	def wr(self,data):
		if self.s:
			if data[-1]!='\n': 
				data+="\n"
			self.s.send(data.encode('utf-8'))
		else:
			print("ERROR: IP socket not open! Unable to write !")

	def is_connected(self):
		if self.s : 
			return True
		else:
			return False

	def rd(self,buflen=1024):
		if self.is_connected():
			r=' ' 
			data=''
			while r!='\n':
				data+=str(self.s.recv(buflen),'utf-8')
				r=data[-1]
			return data[:-1]
		else:
			print("ERROR: IP socket not open! Unable to read !")
		return ""

	def qr(self,data,buflen=1024):
		if self.is_connected():
			self.wr(data)
			return self.rd(buflen=buflen)
		else:
			print("ERROR: IP socket not open! Unable to query !")
		return ""

################################################################################
class socket_gpib():
	def __init__(self,address,chn=None):
		address=int(address)
		self.s=None
		try:
			present=gpib.listener(0,address)
			
			if present:
				self.s=gpib.dev(0,address)
			else:
				print("ERROR: GPIB dev not present")
				return None
		except:
			print("ERROR: GPIB error")

	def is_connected(self):
		if self.s: 
			return True
		else:
			return False

	def wr(self,data):
		if self.is_connected():
			if data[-1]!='\n': 
				data+="\n"
			gpib.write(self.s,data)
		else:
			print("ERROR: GPIB socket not open! Unable to write !")

	def rd(self,buflen=1024):
		if self.is_connected():
			data=gpib.read(self.s,buflen)
			return data[:-1]
		else:
			print("ERROR: GPIB socket not open! Unable to read !")
		return ""

	def qr(self,data,buflen=1024):
		if self.is_connected():
			self.wr(data)
			return self.rd(buflen=buflen)
		else:
			print("ERROR: GPIB socket not open! Unable to query !")
		return ""


################################################################################
class socket_uart():
	def __init__(self,address,chn=None):
		import serial
		address=address
		self.s=None
		try:
			self.s=serial.Serial(address,57600,timeout=3)
		except:
			print("ERROR: UART error")

	def is_connected(self):
		if self.s: 
			return True
		else:
			return False

	def wr(self,data):
		if self.is_connected():
			self.s.write(data)
		else:
			print("ERROR: UART socket not open! Unable to write !")
	
	def rd(self,buflen=1):
		if self.is_connected():
			data=self.s.read(buflen)
			if data:
				return data
			else:
				print("ERROR: cannot receive data from UART socket!")
				return ""
		else:
			print("ERROR: UART socket not open! Unable to read !")
		return ""

	def qr(self,data,buflen=1):
		if self.is_connected():
			self.wr(data)
			data=self.rd(buflen=buflen)
		else:
			print("ERROR: UART socket not open! Unable to query !")
		return ""

if __name__=="__main__":
	print("This program is not runable")
