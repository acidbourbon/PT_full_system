#!/usr/bin/env python3

"""@package docstring
Documentation for this module.

More details.
"""

import string
from sockets import socket_ip,socket_gpib,socket_uart,KNOWN_SOCKETS_TYPES

REGISTERED_SOCKETS=[]

class device(object):
	"""This class is abstract clas for any instrument

	It provides comunication methods.
	"""
	def __init__(self,address,chn=None):
		"""The constructor."""
		# address
		address_split=address.split(":")
		if len(address_split)<2:
			print("ERROR: Wrong device address")
			return None

		_socket_type=address_split[0].lower()
		_socket_address=address_split[1]
		_socket_port=None
		if len(address_split)>2:
			_socket_port=int(address_split[2])

		if not _socket_type in KNOWN_SOCKETS_TYPES:
			print("ERROR: Unknown socket type %s"%_socket_type)
			return None

		socket={'type':_socket_type, 'address':_socket_address, 'port':_socket_port}
		s=self._look_for_socket(socket)
		if s!=None:
			print("reusing socket")
			self._socket=s
		else:
			if _socket_type=="ip": 
				self._socket=socket_ip(ip=_socket_address,port=_socket_port)
				socket['socket']=self._socket
				REGISTERED_SOCKETS.append(socket)
			elif _socket_type=="gpib": 
				self._socket=socket_gpib(address=_socket_address)
				socket['socket']=self._socket
				REGISTERED_SOCKETS.append(socket)
			elif _socket_type=='uart':
				self._socket=socket_uart(address=_socket_address)
				socket['socket']=self._socket
				REGISTERED_SOCKETS.append(socket)
				
	def _look_for_socket(self,socket):
		"""Check if socket with given parameters was already created."""
		for s in REGISTERED_SOCKETS:
			if s['type']==socket['type'] and\
				s['address']==socket['address'] and\
				s['port']==socket['port']:
				return s['socket']
		return None 

	def is_connected(self):
		return self._socket.is_connected()

	def wr(self,data):
		self._socket.wr(data)

	def rd(self,buflen=1024):
		return self._socket.rd(buflen=buflen)

	def qr(self,data,buflen=1024):
		return self._socket.qr(data,buflen=buflen)

	def print_idn(self):
		print(self.qr('*IDN?'))

	def get_idn(self):
		return self.qr('*IDN?')



