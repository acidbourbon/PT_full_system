def scaler_trend_plot(TDClist,channellist,trend_duration,data_dir, measure_time=1):
    trend_scan_Nsteps = 60*60*trend_duration
    #data_dir = "/workdir/jupyter/Dlab_2021_tot_data_taking_data"
    
   
    from matplotlib import pyplot as plt
    #%matplotlib inline
    from IPython.display import clear_output
    import time
    import matplotlib.dates as mdates
    import datetime 
    import tdc_daq as td

    starttime = round(time.time() * 1000) 
    print(starttime)
    # get scaler rates   as simple estimate of noise:   
    scaler_list_trend_channel = [ []  for i in range(len(channellist)*len(TDClist))]
    timestamps = []

    for p in range(0,trend_scan_Nsteps):
        for TDC in TDClist:
            scaler_rates_MDC = td.scaler_rate(TDC,channellist,0.01)        
            for ch in range(0,len(scaler_rates_MDC)):  
                scaler_list_trend_channel[ch+TDClist.index(TDC)*len(channellist)] += [ scaler_rates_MDC[ch] ]  
            timestamps += [ datetime.datetime.now() ]
            print(".", end=" ")
            ###########################################################
            ####plot trends each 5 minutes:
            print(scaler_list_trend_channel[0])
            plt.figure(num=None, figsize=(22, 8), dpi=100, facecolor='w', edgecolor='k')      
            plt.gcf().autofmt_xdate()
               
            if p % 3 == 0:
                # now call function we defined above
                clear_output(wait=True)
                for ch in range(0,len(channellist)):
                    plt.errorbar( timestamps,scaler_list_trend_channel[ch+TDClist.index(TDC)*len(channellist)], yerr=None, xerr=None) 
#                     # fmt='o:', alpha=0.9,label = "{:s} channel {:d}".format(TDC,channellist[ch]))                        
 
#                         # beautify the x-labels
#                     plt.xlabel("time ")
#                     plt.yscale('log')
#                     plt.ylim(0.1,1e10)
#                     plt.ylabel(" scaler rates")
#                     plt.savefig('{:s}/MBO_rate_trend{:d}.png'.format(data_dir,starttime), dpi=100)
#                     plt.legend()  
#                     plt.grid(axis='y',color='grey',which='both')
                    plt.show()
                        
  
 