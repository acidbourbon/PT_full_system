#!/usr/bin/env python
# -*- coding: utf-8 -*-
from a81150a import a81150a
#from a81150a_virtual import a81150a_virtual
#from time import sleep

class a81150a_fe(a81150a):
	def __init__(self,ip):
		#self.log=log.log
		self.conf=None
		self.go_hardware(ip)
		#self.log('81550A FE class initialized',1)
		print('81550A FE class initialized')
	
	#def go_virtual(self):
	#	self.__class__.__bases__ =(a81150a_virtual,)
	#	a81150a_virtual.__init__(self,self.log)
		
	def go_hardware(self,ip):
		self.__class__.__bases__ =(a81150a,)
		a81150a.__init__(self,address=ip,chn=None)
	
	def init_dev_hiamp(self,chn=1):
		#self.log('-> Configuring 81550A for high amplitude (>100mV) output.',1)
		print('-> Configuring 81550A for high amplitude (>100mV) output.')
		self.reset_dev()
		self.set_fg_shape(chn,'SQUare')
		self.set_fg_duty_cycle(chn,50.)
		self.set_fg_high(chn,5.e-2)
		self.set_fg_low(chn,0.)
		#self.set_fg_frequency(chn,300e3)
		#self.set_fg_delay(chn,10.5e-9)  ##salt
		#self.set_fg_delay(chn,9.987e-6)   ##lumi on 81150A
		self.set_polarity(True)
		self.set_coupling(chn,1)
		self.set_coupling(chn,0)
		self.set_output_state(chn,1)
		while(not self.get_output_state(chn)):
			pass
		self.conf='High'
		#self.log('-> Done.',1)
		print('-> Done.')
	
	def init_dev_lowamp(self,chn=1):
		#self.log('-> Configuring 81550A for low amplitude (<100mV) output.',1)
		print('-> Configuring 81550A for low amplitude (<100mV) output.')
		self.reset_dev()
		for i in range(1,3):
			self.set_fg_shape(i,'SQUare')
			self.set_fg_offset(i,0.)
			self.set_fg_duty_cycle(i,50.)
			#self.set_fg_frequency(i,300e3)
			#self.set_fg_delay(i,10.5e-9)  ##salt
			#self.set_fg_delay(i,9.987e-6)   ##lumi on 81150A
		#self.set_fg_delay(1,3.33e-7)   ##pasttrec on 81150A
		self.set_fg_high(1,.0)
		self.set_fg_low(1,-.1)
		self.set_fg_high(2,.1)
		self.set_fg_low(2,0.)
		self.set_coupling(1,1)
		self.set_coupling(1,0)
		self.set_polarity(False)
		self.set_channel_sum(1)
		self.set_fg_high(2,0.105)
		self.set_output_state(1,1)
		
		while(not self.get_output_state(1)):
			pass
		self.conf='Low'
		#self.log('-> Done.',1)
		print('-> Done.')

	def set_amp(self,amp,freq_meas):
		if amp<1e-3:
			return (False,1e-3)
		if amp>5.:
			return (False,5.)
		
		if amp<1.e-1:
			if not self.conf=='Low':
				self.init_dev_lowamp(1)
			#self.log('Low amplitude (<100mV) config used for amp=%e V.'%amp,2)
			self.set_fg_frequency(1,freq_meas)
			self.set_fg_frequency(2,freq_meas)
			print('Low amplitude (<100mV) config used for amp=%e V.'%amp)
			self.set_fg_high(2,(amp+0.1))
			self.set_fg_low(2,0.)
			self.set_fg_high(1,.0)
			self.set_fg_low(1,-.1)
		else:
			if not self.conf=='High':
				self.init_dev_hiamp(1)
			#self.log('High amplitude (>100mV) config used for amp=%e V.'%amp,2)
			self.set_fg_frequency(1,freq_meas)
			print('High amplitude (>100mV) config used for amp=%e V.'%amp)
			self.set_fg_high(1,amp)
		
		return (True,amp)
	
	def set_polarity(self,polarity):
		if self.conf=='Low':
			self.set_output_polarity(1,not polarity)
			self.set_output_polarity(2,polarity)
		else:
			self.set_output_polarity(1,polarity)
		
