
import os
import db
import tdc_daq
from time import sleep
import numpy as np
import matplotlib.pyplot as plt
import warnings

from trbnet import TrbNet

lib = '/trbnettools/trbnetd/libtrbnet.so'
host = os.getenv("DAQOPSERVER")

t = TrbNet(libtrbnet=lib, daqopserver=host)

global_settings = db.get_global_settings()
slow_control_log = 0
if ("slow_control_log" in global_settings):
	if (global_settings["slow_control_log"] == 1):
		slow_control_log = 1

slow_control_log_file = "./slow_control.log"

spi_queue = 0
spi_mem = {}
gain_map = {0.67: 0b11, 1: 0b10, 2: 0b01, 4: 0b00}
pt_map = {10: 0b00, 15: 0b01, 20: 0b10, 35: 0b11}

class HelperFunctions:	
	def getCHIPID(CONN,CHIP):
		return (CONN -1) * 2 + CHIP
	def init_queue(TDC,CONN,CHIP):
		global spi_mem
		if ( not( TDC in spi_mem ) ):
			spi_mem[TDC] = {}
		if ( not( CONN in spi_mem[TDC] ) ):
			spi_mem[TDC][CONN] = {}
		if ( not( CHIP in spi_mem[TDC][CONN] ) ):
			spi_mem[TDC][CONN][CHIP] = []

def spi(TDC_str,CONN,CHIP, data_list, **kwargs):
	""" 
	Transmit data to a specific PASTTREC using old-style notation.

	Parameters
	TDC_str (str) + Address of associated TDC.

	CONN (int) - Number of PASTTREC connection.

	CHIP (int) - Number of PASTTREC inside a connection.

	data_list (list(int)) - Data to be transmitted. Each entry should contain the address of the target register (bits from 11 to 8) and actual data (bits from 7 to 0)
	"""
	CHIP_ID = HelperFunctions.getCHIPID(CONN, CHIP)
	f = ""
	if (slow_control_log):
		f = open(slow_control_log_file,"a")
	TDC = int(TDC_str,16)	
	HelperFunctions.init_queue(TDC,CONN,CHIP)
	if spi_queue:
		spi_mem[TDC][CONN][CHIP] += data_list
	else:
		my_data_list = spi_mem[TDC][CONN][CHIP] + data_list
		spi_mem[TDC][CONN][CHIP].clear() # empty queue
		for data in my_data_list:
			# writing one data word, append zero to the data word, the chip will get some more SCK clock cycles
			address_past = (CHIP_ID << 4) + ((data & 0xF00) >> 8 )
			data_past = data & 0xFF
			t.trb_register_write(TDC, 0xA200 + address_past, data_past )
			sleep(1E-4)
			if (slow_control_log):
				f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xA200 + address_past, data_past ))
	if (slow_control_log):
		f.close()

def spi_mdc_mbo(TDC_str,ADDR, data):
	""" 
	Write data to a specific TDC register. Supports querying.

	Parameters
	TDC_str (str) - Address of associated TDC.

	ADDR (int) - Address of target register.

	data (int) - Data to be written.
	"""
	if (slow_control_log):
		f = open(slow_control_log_file,"a")
	TDC = int(TDC_str,16)
	HelperFunctions.init_queue(TDC,"mdc_mbo","mdc_mbo")
	if spi_queue:
		spi_mem[TDC]["mdc_mbo"]["mdc_mbo"] += [(ADDR, data)]
	else:
		my_data_list = spi_mem[TDC]["mdc_mbo"]["mdc_mbo"] + [(ADDR, data)]
		spi_mem[TDC]["mdc_mbo"]["mdc_mbo"].clear() # empty queue
		for address, value in my_data_list:
			t.trb_register_write(TDC, address, value )
			print("T: %04x %04x %08x" % (TDC, address,value))
			if (slow_control_log):
				f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, address, value ))
	if (slow_control_log):
		f.close()
        #activate written registers:
	#t.trb_register_write(TDC, 0xAA00, 1 )

   

def spi_set_pasttrec_register(TDC_str,pasttrec,reg, data):
	"""
	Set a value to a specific PASTTREC register.

	Parameters
	TDC_str (str) - Address of associated TDC.

	pasttrec (int) - Number of PASTTREC ASIC [0-3].

	reg (int) - Address of PASTTREC register [0x0 - 0xD].

	data (int) - Data to be written [0x00 - 0xFF].
	"""
	spi_mdc_mbo(TDC_str, 0xA200 + ((0xF & pasttrec) << 4) + (0xF & reg),(0xFF & data))
	#spi_mdc_mbo(TDC_str, 0xAA02 + ((0xF & pasttrec) << 4),(0xFF & data) + ((0xF & reg) << 8))

def spi_set_pasttrecs_register(TDC_str,reg, data):
	"""
	The same as spi_set_pasttrec_register(), but for all associated with specific TDC PASTTRECs at once.

	Parameters
	TDC_str (str) - Address of associated TDC.

	reg (int) - Address of PASTTREC register [0x0 - 0xD].

	data (int) - Data to be written [0x00 - 0xFF].

	"""
	#spi_mdc_mbo(TDC_str, 0xAA0A, (0xFF & data) + ((0xF & reg) << 8))
	spi_mdc_mbo(TDC_str, 0xA200 + (0xF & reg),(0xFF & data))
	spi_mdc_mbo(TDC_str, 0xA210 + (0xF & reg),(0xFF & data))
	spi_mdc_mbo(TDC_str, 0xA220 + (0xF & reg),(0xFF & data))
	spi_mdc_mbo(TDC_str, 0xA230 + (0xF & reg),(0xFF & data))
	

def load_set_to_pasttrec(TDC_str, pasttrec, addr, len):
	"""
	Load set of commands from module memory to one PASTTREC.

	Parameters
	TDC_str (str) - TDC address.

	pasttrec (int) - PASTTREC number

	addr (int) - Address of the first command in module memory.

	len (int) - Number of commands in a set.
	"""
	spi_mdc_mbo(TDC_str, 0xAA01 + (pasttrec<<4), ((0x3F & len) << 8) + (0xFF & addr))

def load_set_to_pasttrecs(TDC_str, addr, len):
	"""
	The same as load_set_to_pasttrec(), but for all PASTTRECs associated the given TDC at once.

	Parameters
	TDC_str (str) - TDC address.

	addr (int) - Address of the first command in module memory.

	len (int) - Number of commands in a set.
	"""
	spi_mdc_mbo(TDC_str, 0xAA09, ((0x3F & len) << 8) + (0xFF & addr))

def reset_board(TDC_str,CONN=0):
	"""
	Performs a soft reset of the PASTTREC FPGA module (without interruption of all other systems)

	Parameters
	TDC_str (str) - Address of associated TDC.

	CONN (int) - Not used. For back-compatibility only.

	"""
	spi_mdc_mbo(TDC_str, 0xAA00,0)
 
def reset_boards(TDC_strs,CONN=0):
	"""
	The same as reset_board(), but for a list of TDCs.

	Parameters
	TDC_strs (list(str)) - An array of associated TDC`s addresses.

	CONN (int) - Not used. For back-compatibility only.

	"""
	for TDC_str in TDC_strs:
		spi_mdc_mbo(TDC_str, 0xAA00,0)

def reset_board_by_name(board_name):
	"""
	The same as reset_board().

	Parameters
	board_name (str) - Board name.

	"""
	board_info = db.find_board_by_name(board_name)
	tdc_addr = board_info["tdc_addr"]
	if tdc_addr[0:2].lower() == "0x":
		reset_board(tdc_addr)

def set_threshold(TDC,CONN,CHIP,THR):
	"""
	Set a threshold value of specific PASTTREC

	Parameters
	TDC (str) - Address of associated TDC.

	CONN (int) - PASTTREC connection number.

	CHIP (int) - PASTTREC chip number.

	THR (int) - New threshold value.

	"""

	spi_set_pasttrec_register(TDC, HelperFunctions.getCHIPID(CONN,CHIP), 0x3, 0xFF & THR)

def set_threshold_for_board(TDC,conn,thresh, new_style = False):
	"""
	The same as set_threshold(), but for all PASTTRECs associated with specific TDC.

	Parameters
	TDC (str) - Address of associated TDC.

	CONN (int) - PASTTREC connection number. Not used if the new style is used.

	thresh (int) - New threshold value

	new_style (boolean) - If false, only PASTTRECs, associated with the specific connection, are affected. (for back compatibility only). If true, all PASTTRECs associated with specific TDC are affected.
	"""
	if not new_style:
		spi_set_pasttrec_register(TDC, HelperFunctions.getCHIPID(conn,0), 0x3, 0xFF & thresh)
		spi_set_pasttrec_register(TDC, HelperFunctions.getCHIPID(conn,1), 0x3, 0xFF & thresh)
	else:
		spi_set_pasttrecs_register(TDC, 0x3, 0xFF & thresh)
   
def set_threshold_for_board_by_name(board_name,thresh, new_style = False):
	"""
	The same as set_threshold_for_board().

	Parameters
	board_name (str) - Name of the associated board.

	thresh (int) - New threshold value.

	new_style (boolean) - If false, only PASTTRECs, associated with the specific connection, are affected. (for back compatibility only). If true, all PASTTRECs associated with specific TDC are affected.
	"""
	board_info = db.find_board_by_name(board_name)
	conn = board_info["tdc_connector"]
	tdc_addr = board_info["tdc_addr"]
	set_threshold_for_board(tdc_addr,conn,thresh, new_style)

def slow_control_test(board_name): 
	"""
	Performs a slow control test for the specified board.

	Parameters
	board_name (str) - Name of the target board.

	"""

	scan_time = 0.2
	board_info = db.find_board_by_name(board_name)
	channels	 = board_info["channels"] # zero based 
	TDC				= board_info["tdc_addr"]
	connector	= board_info["tdc_connector"]
	db.enable_board(board_name)
	init_board_by_name(board_name)
	print( "slow control test of board "+board_name )
	set_threshold_for_board(TDC,connector,0)
	rates_lo_thr = tdc_daq.scaler_rate(TDC,channels,scan_time)
	set_threshold_for_board(TDC,connector,0xFF)
	rates_hi_thr = tdc_daq.scaler_rate(TDC,channels,scan_time)
	state_hi_thr = tdc_daq.read_ch_state(TDC,channels)
	print( "rates low thr" )
	print( rates_lo_thr )
	print( "rates high thr" )
	print( rates_hi_thr )
	print( "state high thr" )
	print( state_hi_thr )
	## restore threshold again - a bit dirty but faster than complete init again
	setup		 = db.get_setup_json()
	#pktime		= setup["asic_settings"]["default"]["pktime"]
	#gain			= setup["asic_settings"]["default"]["gain"]
	threshold = setup["asic_settings"]["default"]["threshold"]
	#standby_pktime		= setup["asic_settings"]["standby"]["pktime"]
	#standby_gain			= setup["asic_settings"]["standby"]["gain"]
	standby_threshold = setup["asic_settings"]["standby"]["threshold"]
	standby = False
	if "standby" in board_info:
		if board_info["standby"]:
			standby=True
	if standby:
		set_threshold_for_board(TDC,connector,standby_threshold)
	else:
		set_threshold_for_board(TDC,connector,threshold)
	## end of restore threshold
	if state_hi_thr == [1]*len(channels) and rates_hi_thr == [0]*len(channels) and rates_lo_thr != [0]*len(channels):
		return 1
	else:
		return 0

def slow_control_test_boards(board_list): 
	"""
	Performs a slow control test for specified boards.

	Parameters
	board_list (list(str)) – Names of target boards.
	"""
	test_results = {}
	for board_name in board_list:
		test_results[board_name] = slow_control_test(board_name)
	print( test_results )
	return test_results

def set_baseline( TDC, channel,value): 
	"""
	Set a baseline level for one of the TDC channels.

	Parameters
	TDC (str) - A TDC address.

	channel (int) - Number of the channel [0 - 31].

	value (int) - New value of baseline level [-15,15].

	"""
	spi_set_pasttrec_register(TDC, channel // 8, 0x4 + channel%8, 0xFF & (15 + value))

def set_all_baselines( TDC, channels, values): # channels and values have to have same dimensions
	"""
	Set baseline levels for an array of TDC channels.

	Parameters
	TDC (str) - A TDC address.

	channels (list(int)) - Array of channel numbers.

	values (list(int)) - Array of new values of baseline levels.
	"""
	for i, ch in enumerate(channels):
		set_baseline(TDC,ch,int(values[i]))

def set_all_baselines_to_same_value( TDC, value): # channels and values have to have same dimensions
	"""
	Set the same baseline level for all channels of specified TDC.

	Parameters
	TDC (str) - A TDC address.

	value (int) - New value of baseline levels..
	"""
	for ch_n in range(8):
		spi_set_pasttrecs_register(TDC, 0x4 + ch_n, 0xFF & (value + 15))
		#t.trb_register_write(int(TDC,16), 0xA200 + ch_n%8 + 4 + (int(ch_n/8) << 4), value + 15 )

def init_chip(TDC,CONN,CHIP,pktime,GAIN,thresh, baseline_sel=0b1):
	""" 
	Performs an initialization of specific PASTTREC:

	Send a soft reset command

	Apply the specified peaking time, gain, and threshold.

	Parameters
	TDC (str) - An associated TDC.

	CONN (int) - A PASTTRECs connection number.

	CHIP (int) - A PASTTRECs chip number.

	pktime (int) - A value of peaking time, that will be applied.

	GAIN (int) - A value of gain, that will be applied.

	thresh (int) - A value of the threshold, that will be applied.

	baseline_sel (int) - A baseline selection option. For details see the PASTTREC documentation. Usually, should be the same as the default value.
	"""
	global spi_queue
	spi_queue = 1
	reset_board(TDC)
	set_threshold(TDC,CONN,CHIP,thresh)
	spi_set_pasttrec_register(TDC, HelperFunctions.getCHIPID(CONN,CHIP), 0x0, ((baseline_sel & 1) << 4) + (gain_map[GAIN] << 2) + (pt_map[pktime]))
	board_info = db.find_board_by_tdc_connector(TDC,CONN)
	board_name = board_info["name"] 
	board_channels = board_info["channels"] 
	calib = db.get_calib_json_by_name(board_name)
	if ("baselines" in calib):
		board_baselines = calib["baselines"]
		channels = board_channels[0 + 8*CHIP:9 + 8*CHIP]
		values	 = board_baselines[0 + 8*CHIP:9 + 8*CHIP]
		set_all_baselines(TDC,channels,values)
	spi_queue = 0
	set_threshold(TDC,CONN,CHIP,thresh)

def init_board(TDC,conn,pktime,gain,thresh, new_style=True, baseline_sel=0b1):
	""" 
	The same as init_chip(), but for several PASTTRECs at once.

	Parameters
	TDC (str) - An associated TDC.

	conn (int) - A PASTTRECs connection number.

	pktime (int) - A value of peaking time, that will be applied.

	gain (int) - A value of gain, that will be applied.

	thresh (int) - A value of the threshold, that will be applied.

	new_style (boolean) - If false, only PASTTRECs, associated with the specific connection, are affected. (for back compatibility only). If true, all PASTTRECs associated with specific TDC are affected.

	baseline_sel (int) - A baseline selection option. For details see the PASTTREC documentation. Usually, should be the same as the default value.
	"""
	global spi_queue
	spi_queue = 1
	reset_board(TDC)
	if (not new_style):
		spi_set_pasttrec_register(TDC, HelperFunctions.getCHIPID(conn,0), 0x0, ((baseline_sel & 1) << 4) + (gain_map[gain] << 2) + (pt_map[pktime]))
		spi_set_pasttrec_register(TDC, HelperFunctions.getCHIPID(conn,1), 0x0, ((baseline_sel & 1) << 4) + (gain_map[gain] << 2) + (pt_map[pktime]))
	else:
		spi_set_pasttrecs_register(TDC, 0x0, ((baseline_sel & 1) << 4) + (gain_map[gain] << 2) + (pt_map[pktime]))
	spi_queue = 0
	set_threshold_for_board(TDC, conn, thresh, new_style=new_style) 

def init_active_boards(pktime=-1,gain=-1,threshold=-1):
	"""
	The same as init_board(), but for all active boards.

	Parameters
	pktime (int) - A value of peaking time, that will be applied.

	gain (int) - A value of gain, that will be applied.

	threshold (int) - A value of the threshold, that will be applied.
	"""
	init_boards_by_name(db.active_board_list(),pktime,gain,threshold)

def init_boards_by_name(board_list,pktime=-1,gain=-1,threshold=-1):
	"""
	The same as init_board(), but for a specified list of boards.

	Parameters
	board_list (list(str)) - A list of target board`s names.

	pktime (int) - A value of peaking time, that will be applied.

	gain (int) - A value of gain, that will be applied.

	threshold (int) - A value of the threshold, that will be applied.
	"""
	setup		 = db.get_setup_json()
	if(pktime == -1): 
		pktime		= setup["asic_settings"]["default"]["pktime"]
	if(gain == -1):
		gain			= setup["asic_settings"]["default"]["gain"]
	if(threshold == -1):
		threshold = setup["asic_settings"]["default"]["threshold"]
	standby_pktime		= setup["asic_settings"]["standby"]["pktime"]
	standby_gain			= setup["asic_settings"]["standby"]["gain"]
	standby_threshold = setup["asic_settings"]["standby"]["threshold"]
	for board_name in board_list:
		#print("init board "+board_name)
		board_info = db.find_board_by_name(board_name)
		conn = board_info["tdc_connector"]
		tdc_addr = board_info["tdc_addr"]
		standby = False
		if "standby" in board_info:
			if board_info["standby"]:
				standby=True
		if tdc_addr[0:2].lower() == "0x":
			if standby:
				init_board(tdc_addr,conn,standby_pktime,standby_gain,standby_threshold)
			else:
				init_board(tdc_addr,conn,pktime,gain,threshold)

def init_board_by_name(board,pktime=-1,gain=-1,threshold=-1):
	""" 
	The same as init_boards_by_name(), but for one board.

	Parameters
	board (str) - A target board name.

	pktime (int) - A value of peaking time, that will be applied.

	gain (int) - A value of gain, that will be applied.

	threshold (int) - A value of the threshold, that will be applied.
	"""
	return init_boards_by_name([ board ],pktime,gain,threshold)

def found_baselines_for_board(board, scanning_time = 0.2, plot=False, apply_res=False, thresh=0):
	"""
	Found a baseline level for all channels of a specific board with a noise method.

	Parameters
	board (str) - A TDC address.

	scanning_time (float) - Duration of each step during data acquisition

	plot (boolean) - if true, plot the noise level versus baseline for each channel.

	apply_res (boolean) - if true, apply each baseline level to an estimated value.

	"""
	return found_baselines_for_boards([board], scanning_time, plot, apply_res, thresh)[board]

def found_baselines_for_boards(boards, scanning_time = 0.2, plot=False, apply_res=False, thresh=0):
	"""
	The same as found_baselines_for_board() but for a list of boards.

	Parameters
	boards (list(str)) - A list of TDC`s addresses.

	scanning_time (float) - Duration of each step during data acquisition.

	plot (boolean) - if true, plot the noise level versus baseline for each channel.

	apply_res (boolean) - if true, apply each baseline level to an estimated value.
	"""

	channels = list(range(32))
	for board in boards:
		set_threshold_for_board_by_name(board, thresh, new_style=True)
	scalers = np.empty((len(boards), len(channels), 31))
	for baseline in range(-15,15 + 1):
		for nboard, board in enumerate(boards):
			board_info = db.find_board_by_name(board)
			tdc_addr = board_info["tdc_addr"]
			set_all_baselines_to_same_value(tdc_addr,baseline)
			print(baseline)
			sleep(1)

			
			scalers[nboard, :, baseline + 15] = - np.array(tdc_daq.read_spikes(tdc_addr,channels))
		sleep(scanning_time)
		for nboard, board in enumerate(boards):
			board_info = db.find_board_by_name(board)
			tdc_addr = board_info["tdc_addr"]
			scalers[nboard, :, baseline + 15] += np.array(tdc_daq.read_spikes(tdc_addr,channels))
		scalers[:, :, baseline + 15] += (scalers[:, :, baseline + 15] < 0) * (2**24)
		scalers[:, :, baseline + 15] /= scanning_time
	if plot:
		fig, ax = plt.subplots(7 * len(boards),5)
		fig.set_size_inches(18.5, 18.5 * len(boards))
		plt.tight_layout()
	res = {}
	baselinearr = np.arange(-15, 15+1)# np.array(list(range(-15,15+1)))
	for nboard,board in enumerate(boards):
		res[board] = {}
		for nch,ch in enumerate(channels):
			values = scalers[nboard, nch, :]
			if np.all(values == 0):
				mean, rms = 16, -1
				warnings.warn("No data from channel {} of board {}".format(ch,board))
				if plot:
					ax[nboard * 7 + nch // 5, nch % 5].set_title("Board {} ch {}".format(board, ch))
					ax[nboard * 7 + nch // 5, nch % 5].set_ylim([0, 1])
					ax[nboard * 7 + nch // 5, nch % 5].plot(np.linspace(0,1,100),np.linspace(0,1,100), color="r")
					ax[nboard * 7 + nch // 5, nch % 5].text(0,0.7,"DEAD")
			else:
				mean = np.dot(values, baselinearr)/np.sum(values)
				rms = np.sqrt(np.dot(np.power(baselinearr-mean,2), values)/np.sum(values))
				if plot:
					ax[nboard * 7 + nch // 5, nch % 5].scatter(baselinearr,values)
					ax[nboard * 7 + nch // 5, nch % 5].set_yscale("log")
					ax[nboard * 7 + nch // 5, nch % 5].set_ylim([0.5, np.amax(values)])
					ax[nboard * 7 + nch // 5, nch % 5].set_title("Board {} ch {}".format(board, ch))
					ax[nboard * 7 + nch // 5, nch % 5].axvline(x = mean, c="r")
					ax[nboard * 7 + nch // 5, nch % 5].axvline(x = mean-3*rms, c="g")
					ax[nboard * 7 + nch // 5, nch % 5].axvline(x = mean+3*rms, c="g")
			res[board][ch] = {"mean": mean, "rms": rms}
		if apply_res:
			values = [int(res[board][ch]["mean"]) for ch in channels ]
			set_all_baselines(board, channels, values)
	return res
	
def read_PASTTREC_regs(TDC_str, pasttrec):
	"""
	Read the values of PASTTREC registers.

	Parameters
	TDC_str (str) - A TDC address.

	pasttrec (int) - PASTTREC number.
	"""
	def read_reg(TDC_str, reg):
		return "{0:#010x}".format(t.trb_register_read(int(TDC_str,16), reg)[1])
	def read_multibyte(TDC_str, reg):
		raw_data = read_reg(TDC_str, reg)
		return ["0x{}".format(raw_data[i:i+2]) for i in [2,4,6,8]]
	last_byte = read_reg(TDC_str, 0xA0FF)
	if last_byte == "0x00051f00":
		# fast mode is availible
		data = []
		for start_addr in range(0,0xf,4):
			if start_addr != 0xc:
				load_set_to_pasttrec(TDC_str=TDC_str, pasttrec=pasttrec, addr=0xF0 + start_addr, len=4)
				data = data + read_multibyte(TDC_str, 0xA10B)
			else:
				load_set_to_pasttrec(TDC_str=TDC_str, pasttrec=pasttrec, addr=0xFC, len=2)
				data = data + read_multibyte(TDC_str, 0xA10B)[2:4]
		assert len(data) == 14, "Something wrong.."
		return dict(zip(["{0:#3x}".format(el) for el in range(14)], data))
	else:
		# fast mode is not availible
		data = []
		for start_addr in range(0,0xf,4):
			if start_addr != 0xc:
				for offset in range(4):
					t.trb_register_read(int(TDC_str,16), 0xA200 + (pasttrec << 4) + start_addr + offset)
				data = data + read_multibyte(TDC_str, 0xA10B)
			else:
				for offset in range(2):
					t.trb_register_read(int(TDC_str,16), 0xA200 + (pasttrec << 4) + start_addr + offset)
				data = data + read_multibyte(TDC_str, 0xA10B)[2:4]
		assert len(data) == 14, "Something wrong.."
		return dict(zip(["{0:#3x}".format(el) for el in range(14)], data))
