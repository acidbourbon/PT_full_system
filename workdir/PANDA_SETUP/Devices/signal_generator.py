# kate: line-numbers on; tab-indents on; tab-width 2;
#################################################################################################
# FEB_TestSetup signal generator top level configuration class
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
#################################################################################################
#
# This class utilizes Agilent / Keysight 81150A signal generator driver as default.
# If user wants to use other signal generator than Agilent 81150A, it should prepare its own
# driver based on the a81150a class and change the base class to it.
# 
#################################################################################################

# Python imports
# -none-

# Custom imports
try:
	from .a81150a import a81150a
	from .exceptions import SignalGeneratorInvalidConfig
except (ImportError, SystemError, ValueError, ModuleNotFoundError) as e:
	from a81150a import a81150a
	from exceptions import SignalGeneratorInvalidConfig


# ==========================================================================================
# Auxiliary class holding default signal generator configuration
# ==========================================================================================
class signal_generator_defaults:
	# Wave shape, the a81150a,wave_shapes dictionary key
	wave_shape = 'square'
	
	# Wave duty cycle in [%] or None. If None, wave level width is used, default 50
	wave_duty_cycle = None
	
	# Wave high level width in [s], applied only if duty cycle is None, default 1.e-6
	wave_width = 3.e-6
	
	# Wave high level voltage in [V] , default 5.e-2
	wave_high_level = 5.0
	
	# Wave low level voltage in [V]
	wave_low_level = 0.
	
	# Wave frequency in [Hz] , default 100.e3
	wave_frequency = 1.e3
	
	# Wave polarity - the a81150a,wave_polarities dictionary key 'normal'
	wave_polarity ='normal'
	
	# Wave trailing edge, either:
	#  - time in [s] 
	#  - the a81150a.edge_options dictionary key for the minimal or maximal value 
	#  - None if should not be applied
	trailing_edge_time = 'minimum'
	
	# Wave leading edge, either:
	#  - time in [s] 
	#  - the a81150a.edge_options dictionary key for the minimal or maximal value 
	#  - None if should not be applied
	leading_edge_time = 'minimum'
	
	# Output enable - True or False
	output_enable = False
	
	# Complementary output enable - True or False
	complementary_output_enable = False
	
	# List of all available channel numbers
	channel_numbers = [1, 2]


# ==========================================================================================
# Auxiliary class holding setup limits for the maximal and minimal wave voltages
# ==========================================================================================
class setup_wave_limits:
	# Setup upper limit for amplitude or wave high level in [V]
	maximal_high_level = 5.
	
	# Setup lower limit for amplitude or wave low level in [V]
	minimal_low_level = 0.


# ==========================================================================================
# Main signal generator top level configuration class
# ==========================================================================================
class signal_generator( a81150a ):
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Init 
	# Args:
	#  - string containing generator IP address and PORT, build accordingly to the
	#    following pattern: "ip:IP:PORT", eg. "ip:192.168.0.1:5025", as it is
	#    required by the device class
	# Returns:
	#  - nothing
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def __init__(self, ip):
		a81150a.__init__(self, address = ip)
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# PRIVATE METHOD
	# Method converting channel argument from possible type variations into
	# list of channels for which the settings should be applied
	# Args:
	#  - channels - either:
	#                + integer with channel number
	#                + list or tuple of integers (channel numbers)
	# Returns:
	#  - list of integers - channel numbers
	# Raises SignalGeneratorInvalidConfig exception if provided argument is invalid
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def __convert_channels_argument(self, channels):
		# Parse channel argument. If it is integer, make it a single element list
		# If it is a list or tuple, leave it as it is
		# In any other case, return an error
		if type( channels ) is int:
			channels = [ channels, ]
		elif not type( channels ) in (list, tuple):
			raise SignalGeneratorInvalidConfig( 'Wrong channel argument type' )
		
		for channel in channels:
			if not channel in signal_generator_defaults.channel_numbers:
				raise SignalGeneratorInvalidConfig( 'Wrong channel number %d' % channel )
		
		return channels
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Method to initialize the device to the default configuration.
	# This method should be called on the measurement procedure beginning
	# Args:
	#  - channels - either:
	#                + integer with channel number
	#                + list or tuple of integers (channel numbers)
	#               the default settings will be applied to all channels provided
	#               by this argument. Other channels will be left in configuration
	#               provided by the device after software reset
	# Returns:
	#  - nothing
	# Raises SignalGeneratorInvalidConfig exception if provided argument is invalid
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def initialize(self, channels ):
		# Convert channels argument into the list
		channels = self.__convert_channels_argument( channels )
		
		# Apply software reset to device 
		self.reset_device()
		
		# Configure all channels
		for channel in channels:
			# Set default wave shape
			self.write_shape( channel, signal_generator_defaults.wave_shape )
			
			# Set duty cycle of width if duty cycle is None
			if not signal_generator_defaults.wave_duty_cycle is None:
				self.write_duty_cycle( channel, signal_generator_defaults.wave_duty_cycle )
			else:
				self.write_width( channel, signal_generator_defaults.wave_width )
			
			# Set default frequency 
			self.write_frequency( channel, signal_generator_defaults.wave_frequency )
			
			# Set default wave high and low levels
			self.write_high_level( channel, signal_generator_defaults.wave_high_level )
			self.write_low_level( channel, signal_generator_defaults.wave_low_level )
			
			# Set wave polarity
			self.write_output_polarity( channel, signal_generator_defaults.wave_polarity )
			
			# Set trailing and leading times if provided
			if not signal_generator_defaults.trailing_edge_time is None:
				self.write_trailing_edge_time( channel, signal_generator_defaults.trailing_edge_time )
			if not signal_generator_defaults.leading_edge_time is None:
				self.write_leading_edge_time( channel, signal_generator_defaults.leading_edge_time )
			
			# Set channel output enable or disable 
			self.write_output_state( channel, signal_generator_defaults.output_enable )
			self.write_complementary_output_state( channel, signal_generator_defaults.complementary_output_enable )
			
			# Wait until channel output reaches requested state
			while ( self.read_output_state( channel ) != signal_generator_defaults.output_enable ):
				pass
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Method to switch on/off the outputs of the device
	# Args:
	#  - channels - either:
	#                + integer with channel number
	#                + list or tuple of integers (channel numbers)
	#               The output state will be applied to all channels provided
	#               by this argument. Other channels will be left untouched
	#               provided by the device after software reset
	# Returns:
	#  - nothing
	# Raises SignalGeneratorInvalidConfig exception if provided argument is invalid
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def set_output_state(self, channels, state ):
		# Convert channels argument into the list
		channels = self.__convert_channels_argument( channels )
		
		# Configure all channels
		for channel in channels:
			
			# Set channel output enable or disable 
			self.write_output_state( channel, state )
			self.write_complementary_output_state( channel, state )
			
			# Wait until channel output reaches requested state
			while ( self.read_output_state( channel ) != state ):
				pass
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Method to switch on/off the display of the device
	# Args:
	#  - state - either:
	#               + 0/1 - off/on the display
	#               + False/True - off/on the display
	# Returns:
	#  - nothing
	# Raises SignalGeneratorInvalidConfig exception if provided argument is invalid
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def set_display_state(self, state ):
		self.write_display_state(state)
	
	
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Method to set output amplitude at the selected channel
	# Args:
	#  - channels - either:
	#                + integer with channel number
	#                + list or tuple of integers (channel numbers)
	#               the amplitude settings will be applied to all channels provided
	#               by this argument. Other channels amplitude will be left untouched
	#  - amplitude - either:
	#                + float value - high level of the wave given in [V]
	#                + list or tuple of two float values - low and high levels of 
	#                  the wave, both given in [V]
	# Returns:
	#  - nothing
	# Raises SignalGeneratorInvalidConfig exception if provided arguments are 
	# invalid or out of range
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def set_amplitude(self, channels, amplitude):
		# Check amplitude argument type:
		# If it is float, assign it to the wave high level
		# and set wave low level as None
		if type( amplitude ) is float:
			wave_high_level = amplitude
			wave_low_level = None
		
		# Otherwise amplitude argument have to be list or tuple
		# with exactly two elements
		elif type( amplitude ) in (tuple, list):
			if not len( amplitude ) == 2:
				raise SignalGeneratorInvalidConfig( 'Wrong amplitude list length - expected 2, got %d' % len( amplitude ) )
			# Assign high and low levels
			wave_high_level = amplitude[ 1 ]
			wave_low_level = amplitude[ 0 ]
		# Not recognized amplitude argument type
		else:
			raise SignalGeneratorInvalidConfig( 'Wrong amplitude argument type' )
		
		# Check device limits:
		# If low level is given, it have to be within limits and
		# smaller than high level
		if not wave_low_level is None:
			if (
				wave_low_level < setup_wave_limits.minimal_low_level or 
				wave_low_level > setup_wave_limits.maximal_high_level
			):
				raise SignalGeneratorInvalidConfig( 'Wave low level (%.3f) out of range' % wave_low_level )
			if wave_low_level > wave_high_level:
				raise SignalGeneratorInvalidConfig( 'Wave low level (%.3f) higher than high level (%.3f)' % (wave_low_level, wave_high_level ) )
		# Check limits for high level
		if (
			wave_high_level < setup_wave_limits.minimal_low_level or 
			wave_high_level > setup_wave_limits.maximal_high_level
		):
			raise SignalGeneratorInvalidConfig( 'Wave high level (%.3f) out of range' % wave_high_level )
		
		# Convert channels argument into the list
		channels = self.__convert_channels_argument( channels )
		
		# Configure all channels
		for channel in channels:
			# Set low level if given
			if not wave_low_level is None:
				self.write_low_level( channel, wave_low_level )
			
			# Set high level
			self.write_high_level( channel, wave_high_level )
	
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	# Method to set output frequency at the selected channel
	# Args:
	#  - channels - either:
	#                + integer with channel number
	#                + list or tuple of integers (channel numbers)
	#               the amplitude settings will be applied to all channels provided
	#               by this argument. Other channels amplitude will be left untouched
	#  - frequency - wave frequency set to the channel. If None or not given, frequency 
	#                is not changed by this procedure
	# Returns:
	#  - nothing
	# Raises SignalGeneratorInvalidConfig exception if provided arguments are 
	# invalid or out of range
	# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	def set_frequency(self, channels, frequency):
		# Convert channels argument into the list
		channels = self.__convert_channels_argument( channels )
		
		for channel in channels:
			# Set wave frequency
			self.write_frequency( channel, frequency )
			
			# Set default trailing and leading times if provided
			# This setting should be applied each time frequency is changed
			if not signal_generator_defaults.trailing_edge_time is None:
				self.write_trailing_edge_time( channel, signal_generator_defaults.trailing_edge_time )
			if not signal_generator_defaults.leading_edge_time is None:
				self.write_leading_edge_time( channel, signal_generator_defaults.leading_edge_time )
