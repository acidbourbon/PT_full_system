# kate: line-numbers on; tab-indents on; tab-width 2;
#################################################################################################
# FEB_TestSetup Agilent / Keysight 81150A signal generator driver
# 
# FEB_TestSetup - Pasttrec front-end boards (FEB) mass test setup
# Copyright 2021
#    Miroslaw Firlej,  AGH-UST, Krakow, Poland
#    Jakub Moron, AGH-UST, Krakow, Poland
#
#    Requirements:
#      - Python >= 3.7
#      - Agilent 81150A signal generator or different signal generator if the
#        suitable low-level driver is provided
#
#    This file is part of FEB_TestSetup
#
#    FEB_TestSetup is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    FEB_TestSetup is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with FEB_TestSetup.  If not, see <http://www.gnu.org/licenses/>.
#    
#################################################################################################
#
# This class provides unified interface to the signal generator. 
# If user wants to use other signal generator than Agilent 81150A, it should prepare its own
# driver based on this class. 
# User custom driver have to provide exactly the same interface (the same methods) as this class.
# After preparing a dedicated driver, user should change the base class of the signal_generator 
# class.
#
#################################################################################################

# Python imports
# -none-

# Custom imports
try:
	from .device import device
	from .exceptions import A81150aInvalidConfig
except (ImportError, SystemError, ValueError, ModuleNotFoundError) as e:
	from device import device
	from exceptions import A81150aInvalidConfig


# ==========================================================================================
# Main Agilent / Keysight 81150A signal generator driver class
# ==========================================================================================
class a81150a( device ):
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Definition of all possible wave shapes:
	#  - key = name used in code
	#  - value = device command argument
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	wave_shapes = {
		'sinus':		'SINusiod',
		'square':		'SQUare',
		'ramp':			'RAMP',
		'pulse':		'PULSe',
		'noise':		'NOISe',
		'dc':				'DC',
		'user':			'USER',
	}
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Definition of all possible wave polarities:
	#  - key = name used in code
	#  - value = device command argument
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	wave_polarities = {
		'normal':		'NORMal',
		'inverted':	'INVerted',
	}
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Definition of all named edge times shapes:
	#  - key = name used in code
	#  - value = device command argument
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	edge_options = {
		'minimum':		'MINimum',
		'maximum':		'MAXimum',
	}
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Init 
	# Args:
	#  - string containing device IP address and PORT, build accordingly to the
	#    following pattern: "ip:IP:PORT", eg. "ip:192.168.0.1:5025", as it is
	#    required by the device class
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def __init__(self, address ):
		device.__init__(self, address = address )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Apply software reset to the device 
	# Args:
	#  - none
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def reset_device(self):
		self.wr('*RST')
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set wave amplitude 
	# Args:
	#  - channel number (integer)
	#  - amplitude in [V] (float)
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_amplitude(self, channel, amplitude ):
		self.wr( ':VOLTage%d:AMPLitude %.5e' % (channel, amplitude ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set wave offset
	# Args:
	#  - channel number (integer)
	#  - offset in [V] (float)
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_offset(self, chnnel, offset ):
		self.wr( ':VOLTage%d:Offset %.5e' % (channel, offset ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set wave high level
	# Args:
	#  - channel number (integer)
	#  - high level value in [V] (float)
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_high_level(self, channel, high_level_value ):
		self.wr( ':VOLTage%d:HIGH %.5e' % (channel, high_level_value ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set wave low level
	# Args:
	#  - channel number (integer)
	#  - low level value in [V] (float)
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_low_level(self, channel, low_level_value ):
		self.wr( ':VOLTage%d:LOW %.5e' % (channel, low_level_value ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set wave shape
	# Args:
	#  - channel number (integer)
	#  - shape name (string) - the wave_shapes dictionary key (name used in code)
	# Returns:
	#  - nothing
	# Raises A81150aInvalidConfig exception if provided shape_name is invalid
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_shape(self, channel, shape_name ):
		if not shape_name in self.wave_shapes:
			raise A81150aInvalidConfig( 'Invalid shape name "%s"' % repr(shape_name) )
		
		shape_argument = self.wave_shapes[ shape_name ]
		self.wr( ':FUNCtion%d %s' % (channel, shape_argument ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set wave frequency
	# Args:
	#  - channel number (integer)
	#  - frequency in [Hz] (float)
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_frequency(self, channel, frequency ):
		self.wr( ':FREQuency%d %.10e' % (channel, frequency ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set wave duty cycle
	# Args:
	#  - channel number (integer)
	#  - duty cycle in [%] (float)
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_duty_cycle(self, channel, duty_cycle ):
		self.wr( ':FUNCtion%d:PULSe:DCYCle %.5e' % (channel, duty_cycle ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set wave high level width
	# Args:
	#  - channel number (integer)
	#  - width in [s] (float)
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_width(self, channel, width ):
		self.wr( ':FUNCtion%d:PULSe:WIDTh %.10e' % (channel, width ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set output state - enabled or disabled
	# Args:
	#  - channel number (integer)
	#  - output state (boolean):
	#     + 0 / False - channel disabled
	#     + 1 / True - channel enabled
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_output_state(self, channel, state ):
		self.wr( ':OUTPut%d %d' % (channel, state ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set complementary output state - enabled or disabled
	# Args:
	#  - channel number (integer)
	#  - output state (boolean):
	#     + 0 / False - channel disabled
	#     + 1 / True - channel enabled
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_complementary_output_state(self, channel, state ):
		self.wr( ':OUTPut%d:COMPlement %d' % (channel, state ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set display state - enabled or disabled 
	# Args:
	#  - output state (boolean):
	#     + 0 / False - Display OFF
	#     + 1 / True - Display ON
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_display_state(self, state ):
		disp={1:"ON",0:"OFF"}
		self.wr( ':DISPlay %s' % (disp[int(state)]) )
		
		
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set output polarity - normal or inverted
	# Args:
	#  - channel number (integer)
	#  - output polarity (string) - the wave_polarities dictionary key 
	# Returns:
	#  - nothing
	# Raises A81150aInvalidConfig exception if provided polarity is invalid
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_output_polarity(self, channel, polarity ):
		if not polarity in self.wave_polarities:
			raise A81150aInvalidConfig( 'Invalid polarity "%s"' % repr(polarity) )
		
		polarity_argument = self.wave_polarities[ polarity ]
		self.wr( ':OUTPut%d:POLarity %s' % ( channel, polarity_argument ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set output pulse delay respectively to the pulse start (trigger)
	# Args:
	#  - channel number (integer)
	#  - pulse start delay in [s] (float)
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_delay(self, channel, delay):
		self.wr( ':PULSe:DELay%d %e' % (channel, delay ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set wave trailing edge time
	# Args:
	#  - channel number (integer)
	#  - trailing edge, either:
	#     + time in [s] (float)
	#     + option argument (string) - the edge_options dictionary key (allows to
	#                                  set time to minimum or maximum automatically)
	# Returns:
	#  - nothing
	# Raises A81150aInvalidConfig exception if provided trailing edge time is invalid
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_trailing_edge_time(self, channel, trailing_time):
		if type( trailing_time ) is float:
			trailing_argument = '%.10e' % trailing_time
		elif trailing_time in self.edge_options:
			trailing_argument = self.edge_options[ trailing_time ]
		else:
			raise A81150aInvalidConfig( 'Invalid trailing time "%s"' % repr(trailing_time) )
			
		self.wr( ':FUNCtion%d:PULSe:TRANsitioin:TRAiling %s' % (channel, trailing_argument ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Set wave leading edge time
	# Args:
	#  - channel number (integer)
	#  - leading edge, either:
	#     + time in [s] (float)
	#     + option argument (string) - the edge_options dictionary key (allows to
	#                                  set time to minimum or maximum automatically)
	# Returns:
	#  - nothing
	# Raises A81150aInvalidConfig exception if provided leading edge time is invalid
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def write_leading_edge_time(self, channel, leading_time):
		if type( leading_time ) is float:
			leading_argument = '%.10e' % leading_time
		elif leading_time in self.edge_options:
			leading_argument = self.edge_options[ leading_time ]
		else:
			raise A81150aInvalidConfig( 'Invalid leading time "%s"' % repr(leading_time) )
		
		self.wr( ':FUNCtion%d:PULSe:TRANsitioin:Leading %s' % (channel, leading_argument ) )
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Reads back output state - enabled or disabled
	# Args:
	#  - channel number (integer)
	# Returns:
	#  - output state (boolean):
	#     + 0 / False - channel disabled
	#     + 1 / True - channel enabled
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def read_output_state(self, channel ):
		return int(self.qr( ':OUTPut%d?' % channel ))
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Reads back complementary output state - enabled or disabled
	# Args:
	#  - channel number (integer)
	# Returns:
	#  - output state (boolean):
	#     + 0 / False - channel disabled
	#     + 1 / True - channel enabled
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def read_complementary_output_state(self, channel ):
		return int(self.qr( ':OUTPut%d:COMPlement?' % channel ))
	
