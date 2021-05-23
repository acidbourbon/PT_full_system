
def scaler_tren_plot(TDC,channellist,trend_duration,label):
    trend_scan_Nsteps = 60*60*trend_duration
    data_dir = "/workdir/jupyter/Cosy2021_tot_data_taking_data"
 
    #time of one measurement in s
    measure_time=1
    # measure_board_list =  [ "0902", "0905"]  
    measure_board_list =  [ "0902"]

    number_of_TDC_channels  =2
    tdc_channels = list(range(0, number_of_TDC_channels))

    from matplotlib import pyplot as plt
    from IPython.display import clear_output

    import time
    import matplotlib.dates as mdates
    import datetime 
    # from cw_pasttrec_functions import *

    import tdc_daq as td

    starttime = round(time.time() * 1000) 
    print(starttime)
    # get scaler rates for chosen threshold/gain/peaking time as simple estimate of noise:
    scaler_list_trend        =  [ []  for i in range(trend_scan_Nsteps) ] 

    scaler_list_trend_channel = [ []  for i in range(len(channellist))]

    timestamps = []


    for b in range(0,len(measure_board_list)):
     name = measure_board_list[b]
     for p in range(0,trend_scan_Nsteps):
#             scaler_rates = td.scaler_rate_of_board(name,measure_time) 
            scaler_rates = td.scaler_rate(TDC,channellist,1)      
            #print(scaler_rates)
 
            for ch in range(0,len(scaler_rates)):
                scaler_list_trend_channel[ch] += [ scaler_rates[ch] ]
           
            timestamps += [ datetime.datetime.now() ]
            print(".", end=" ")
            ###########################################################
            ####plot trends each 5 minutes:
 
            plt.figure(num=None, figsize=(22, 8), dpi=100, facecolor='w', edgecolor='k')      
            plt.gcf().autofmt_xdate()
                            
            if p % 300 == 0:
                        # now call function we defined above

                        clear_output(wait=True)
 

                        for ch in range(0,len(channellist)):                           
                            plt.errorbar( timestamps,scaler_list_trend_channel[ch],  yerr=None, xerr=None, fmt='o:', alpha=0.9,label = "ch {:d}".format(channellist[ch]) )

                          
                        plt.xlabel("time ")
                        plt.yscale('log')
                        plt.ylabel(" scaler rates") 
                        plt.savefig('{:s}/{:s}_rate_trend{:d}.png'.format(data_dir,label,starttime), dpi=100)
                        plt.legend()  
                        plt.show()
                        
def beep(): 
    import IPython.display as ipd
    import numpy
    t = numpy.linspace(0, 0.5, int(0.6*24090), endpoint=False) # time variable
    x = 0.5*numpy.sin(2*numpy.pi*550*t)    
    ipd.Audio(x, rate=24090, autoplay=True) # load a NumPy array  
    print("piep")