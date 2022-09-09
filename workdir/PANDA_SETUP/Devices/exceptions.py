# kate: line-numbers on; tab-indents on; tab-width 2;
#################################################################################################
# Panda_FEB_TestSetup custom exceptions definition
# 
# Panda_FEB_TestSetup - Pasttrec front-end boards (FEB) mass test setup
# Copyright 2021
#    Miroslaw Firlej,  AGH-UST, Krakow, Poland
#    Jakub Moron, AGH-UST, Krakow, Poland
#
#    Requirements:
#      - Python >= 3.7
#      - Agilent 81150A signal generator or different signal generator if the
#        suitable low-level driver is provided
#
#    This file is part of Panda_FEB_ID
#
#    Panda_FEB_ID is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Panda_FEB_ID is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Panda_FEB_ID.  If not, see <http://www.gnu.org/licenses/>.
#    
#################################################################################################

# Python imports
# -none-

# Custom imports
# -none-

# ==========================================================================================
# Agilent / Keysight 81150A signal generator driver exception
# ==========================================================================================
class A81150aInvalidConfig( Exception ):
	pass

# ==========================================================================================
# High-level signal generator configuration exception
# ==========================================================================================
class SignalGeneratorInvalidConfig( Exception ):
	pass
