
import os
import db
import tdc_daq
from time import sleep

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




black_settings_pt15_g1_thr127 = [
	0x019,
	0x11e,
	0x215,
	0x37f,
	0x40f,
	0x50f,
	0x60f,
	0x70f,
	0x80f,
	0x90f,
	0xa0f,
	0xb0f
]

black_settings_pt20_g1_thr127 = [
	0x01a,
	0x11e,
	0x215,
	0x37f,
	0x40f,
	0x50f,
	0x60f,
	0x70f,
	0x80f,
	0x90f,
	0xa0f,
	0xb0f
]

blue_settings_pt10_g1_thr127 = [
	0x018,
	0x11e,
	0x215,
	0x37f,
	0x40f,
	0x50f,
	0x60f,
	0x70f,
	0x80f,
	0x90f,
	0xa0f,
	0xb0f
]

spi_queue = 0
spi_mem = {}

def getCHIPID(CONN,CHIP):
	return (CONN -1) * 2 + CHIP

def spi(TDC_str,CONN,CHIP, data_list, **kwargs):
	CHIP_ID = getCHIPID(CONN, CHIP)
	f = ""
	if (slow_control_log):
		f = open(slow_control_log_file,"a")

	
	TDC = int(TDC_str,16)
	
	
	if ( not( TDC in spi_mem ) ):
		spi_mem[TDC] = {}
	if ( not( CONN in spi_mem[TDC] ) ):
		spi_mem[TDC][CONN] = {}
	if ( not( CHIP in spi_mem[TDC][CONN] ) ):
		spi_mem[TDC][CONN][CHIP] = []
	
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
			if (slow_control_log):
				f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, 0xA200 + address_past, data_past ))

	if (slow_control_log):
		f.close()

def spi_vova(TDC_str,ADDR, data):
	f = ""
	if (slow_control_log):
		f = open(slow_control_log_file,"a")

	TDC = int(TDC_str,16)
	
	t.trb_register_write(TDC, ADDR, data )
	if (slow_control_log):
		f.write("0x{:04X} 0x{:04X} 0x{:08X}\n".format(TDC, ADDR, data ))

	if (slow_control_log):
		f.close()
		

def reset_board(TDC_str,CONN=0):
	# TDC = int(TDC_str,16)
	spi_vova(TDC_str, 0xAA00,0)
 


def set_threshold(TDC,CONN,CHIP,THR):
	spi(TDC,CONN,CHIP, [ 0x300 + (0xFF & THR)])



def slow_control_test(board_name): #TODO
	
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

	set_threshold_for_board(TDC,connector,127)
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

def set_baseline( TDC, channel,value): #TODO

	chip = db.calc_chip_from_channel(channel)
	conn = db.calc_connector_from_channel(channel)
	# print(chip, conn)
	chip_chan=channel%8

	val	= value + 15 
	chan = chip_chan + 4 

	spi(TDC,conn, chip, [ ((0xF & chan)<<8) + val] )

	return


def set_threshold_for_board(TDC,conn,thresh):
	# set_threshold(TDC,conn,0,thresh)
	# set_threshold(TDC,conn,1,thresh)
	spi_vova(TDC, 0xAA0A, 0x300 + (thresh & 0xFF))
	

def set_threshold_for_board_by_name(board_name,thresh):
	
	setup		 = db.get_setup_json()

	board_info = db.find_board_by_name(board_name)
	conn = board_info["tdc_connector"]
	tdc_addr = board_info["tdc_addr"]
	set_threshold_for_board(tdc_addr,conn,thresh)

	return


def set_all_baselines( TDC, channels, values): # channels and values have to have same dimensions
	#print("set baselines of the following channels")
	#print( channels )
	#print("to the following values")
	#print( values )
	index=0
	for i in channels:
		set_baseline(TDC,i,int(values[index]))
		index+=1
		
	return

def getStAddr(pktime, GAIN):
	if (pktime == 10 and GAIN == 1): start_addr = 0xDC
	if (pktime == 10 and GAIN == 2): start_addr = 0xE0
	if (pktime == 10 and GAIN == 4): start_addr = 0xE4
	if (pktime == 15 and GAIN == 1): start_addr = 0xE8
	if (pktime == 15 and GAIN == 2): start_addr = 0xEC
	if (pktime == 15 and GAIN == 4): start_addr = 0xF0
	if (pktime == 20 and GAIN == 1): start_addr = 0xF4
	if (pktime == 20 and GAIN == 2): start_addr = 0xF8
	if (pktime == 20 and GAIN == 4): start_addr = 0xFC
	return start_addr

def init_chip(TDC,CONN,CHIP,pktime,GAIN,thresh):
	# begin queueing
	spi_queue = 1
	
	start_addr = getStAddr(pktime, GAIN)

	spi_vova(TDC, 0xAA01 + (getCHIPID(CONN,CHIP) << 4), start_addr + (4<<8))
	
	board_info = db.find_board_by_tdc_connector(TDC,CONN)
	board_name = board_info["name"] 
	board_channels = board_info["channels"] 
	calib = db.get_calib_json_by_name(board_name)
	
	if ("baselines" in calib):
		board_baselines = calib["baselines"]
		channels = board_channels[0:9]
		values	 = board_baselines[0:9]
		if CHIP == 1:
			channels = board_channels[8:17]
			values	 = board_baselines[8:17]
		set_all_baselines(TDC,channels,values)
	set_threshold(TDC,CONN,CHIP,thresh)
	return

	# send all at once
	spi_queue = 0
	spi(TDC,CONN,CHIP,[])
	

def reset_board_by_name(board_name):
	board_info = db.find_board_by_name(board_name)
	conn = board_info["tdc_connector"]
	tdc_addr = board_info["tdc_addr"]
	if tdc_addr[0:2].lower() == "0x":
		reset_board(tdc_addr,conn)


def init_board(TDC,conn,pktime,gain,thresh):
	st_addr = getStAddr(pktime, gain)
	sett = (1 << 14) + (4 << 8) + st_addr
	spi_vova(TDC, 0xA002, sett << 16 + sett)
	spi_vova(TDC, 0xA003, sett << 16 + sett)
	reset_board(TDC)
	set_threshold_for_board(TDC, conn, thresh)
	return
 

def slow_control_test_boards(board_list): 
	test_results = {}
	for board_name in board_list:
		answer = slow_control_test(board_name)
		test_results[board_name] = answer

	print( test_results )
	return test_results

def init_active_boards(pktime=-1,gain=-1,threshold=-1):
	return init_boards_by_name(db.active_board_list(),pktime,gain,threshold)

def init_boards_by_name(board_list,pktime=-1,gain=-1,threshold=-1):
	
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
	return

def init_board_by_name(board,pktime=-1,gain=-1,threshold=-1):
	return init_boards_by_name([ board ],pktime,gain,threshold)