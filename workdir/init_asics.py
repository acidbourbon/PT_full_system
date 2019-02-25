#!/usr/bin/env python




import tdc_daq as td
import db
import pasttrec_ctrl as ptc



### disable all daq channels of listed TDCs

td.enable_tdc_channels_of_active_boards()

