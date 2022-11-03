#!/usr/bin/env python
# coding: utf-8

 
#----- default settings for the mass test, don't change:
measure_board_list=[ "4000"]
measure_board_name="4000"
# threshold scan scurve fit quality limit to store results
chisquare_limit = 1000
# PASTTREC ASIC parameters:
pt_pktime = 10
pt_gain = 4
pt_threshold_default = 5

data_output_dicrectory="/workdir/data/pasttrec_quality"


# In[2]:


#%matplotlib notebook  
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pasttrec_ctrl as ptc
import json
import sigproc_kit
import tdc_daq as td
import baseline_calib
#import ROOT
import db
from cw_pasttrec_functions import *
from measTOTs import measTOTs

from scipy.optimize import curve_fit
def sigmoid(x,const,mu,sigma):
  return const/(1+np.exp((x-mu)/sigma))

import time 
start_time = time.time()
def time_convert(sec):
  mins = sec // 60
  sec = sec % 60
  hours = mins // 60
  mins = mins % 60
  print("Time Lapsed = {0}:{1}:{2}".format(int(hours),int(mins),sec))


from my_utils import *
set_width_max_of_jupyterpad()

    
def hist_rms(x,y):
  counts = np.sum(y)
  weights = y / counts
  mean = np.dot(x,weights)
  deviations = x - mean
  return np.sqrt(np.dot(deviations**2,weights))
def list_rms(x):
  mean = sum(x)/len(x)
  deviations =  np.asarray(x) -  np.asarray(mean)
  return np.sqrt(sum(deviations**2) /len(x))
def MeanArrays(xs,ys):
    return np.dot(xs,ys)/sum(ys)
def fwhm(x,y):
  dummy, t1, tot = sigproc_kit.discriminate(x,y,np.max(y)/2.,0,0)
  return tot

def calc_chisquare(meas, sigma, fit):
 test_statistic = 0
 diff = pow(meas-fit, 2.)
 for i in range(9,len(meas)):
  if sigma[i] > 0:
     test_statistic += diff[i] / pow(sigma[i],2.)
  else:
     test_statistic += diff[i]
 return test_statistic


def scurve_scan(serial_no):
    # serial number of PASTTREC, needs to be edit for each PASTTREC tested: 
    serial = serial_no  # "0001"
    import os
    '''
    print("load settings to puls generator RIGOL")
    #pulse generator, set up pulse shape
    os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3AOUTPUT2%20ON'")
    os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3AFREQ%201000'")
    os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3AVOLT%3ALEV%3AHIGH%202000mV'")
    os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3AVOLT%3ALEV%3ALOW%200mV'")
    #os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3AVOLT%3ALEV%3AOFFS%200mV'")
    os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3APULS%3ADEL%200'")
    os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3APULS%3AWIDT%20300n'")
    os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3APULS%3ATRAN%3ALEAD%2025ns'")
    os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3ASOUR2%3APULS%3ATRAN%3ATRA%2050ns'")
    os.system("curl 'http://jspc29:1290/tools/vxi/vxi.pl?192.168.0.42&%3AOUTPUT2%20OFF'")
'''

    # In[3]:

    #switch on Power supply of PASTTREC board:    
    import hameg_PT_Frankfurt as htrb
    import time
    htrb.set_state(1,0)
    htrb.set_volt(1,5.0)
    htrb.set_curr(1,0.5)
    htrb.set_state(1,1)
    time.sleep(2)

   #swicth offf pulser for baseline scan
    from signal_generator import signal_generator
    gen = signal_generator("ip:192.168.0.197:5025")
    gen.initialize((1,2))
    gen.set_output_state((1,2),False)
    
    for name in measure_board_list:
        db.unset_standby_board(name)
        td.enable_tdc_channels_of_active_boards()
        ptc.init_active_boards(10,2,5)  
        #root_name = data_output_dicrectory + "/noise_" + name + ".root"
         

        print(" parallel baseline scan board, ", name)
        
        #baseline_calib.baseline_calib_by_noise(name, dummy_calib=True,individual=True) 
        baseline_calib.baseline_calib_by_noise(name, dummy_calib=True,individual=False)     
        #read baseline scans from database:
        baseline_to_set = [15 for i in range(16)] 
        baseline_rms = [0 for i in range(16)] 
        dummy_calib = db.get_calib_json_by_name(name,dummy_calib=True)
        noise_scan_raw = dummy_calib["noise_scan_raw"]
        noise_range    = dummy_calib["bl_range"]
        # get baseline position from mean of scan
        global hist_rms
        global MeanArrays
        for ch in range(0,8):
                rms = hist_rms(noise_range,noise_scan_raw[ch]) 
                baseline_rms[ch] = rms
                if rms < 5.0:
                   baseline_to_set[ch] = MeanArrays(noise_range,noise_scan_raw[ch]) 
        print(" found baselines :", baseline_to_set)        
        # set found baselines:
        baseline_calib.set_baselines_individual(name, baseline_to_set ) 
        #threshold scan with pulser ON!
        print("switch on pulser, do threshold scan")
        #import rigol as rigol
        #rigol.output_on(2)
        ##### new pulse generator + injector borad swichting input channels of PASTTREC
         # -- laboratory equipment --

        freq = 1000
        #amp=0.06
        amp=0.07
        gen.set_frequency((1,2),freq)
        gen.set_amplitude((1,2),amp)
        gen.set_output_state((1,2),True)
        from PANDAmux import PANDAinjectors
        Injectors = PANDAinjectors()
        BranchCfg = {}
        BranchCfg[0] = {"InjAddr":0,"UserID":data_output_dicrectory+"/"+serial} 
         
        status={0:"err",1:"injectors OK"}
        Injectors.InjObjects[BranchCfg[0]["InjAddr"]].setIndicator(status[1])
        
        board_info = db.find_board_by_name(name)
        channels   = board_info["channels"] # zero based 
        TDC        = board_info["tdc_addr"]
        connector  = board_info["tdc_connector"]
        scan_time = 0.2
      
        ptc.init_board_by_name(name,pt_gain,pt_threshold_default)
        thresholds = list(range(5,30)) #default scan range of threshold
        result_matrix = []
        for thr in thresholds:
            ptc.set_threshold_for_board(TDC,connector,thr)
            rates = []
            print("threshold ",thr)
            for ch in range(0,8):
                Injectors.setActiveChannel(ch) 
               # print(td.scaler_rate(TDC,channels,scan_time))
                ch_rate = td.scaler_rate(TDC,channels,scan_time)[ch]
                rates.append(ch_rate)

            result_matrix.append(rates)


 
                
        #baseline_calib.set_baselines_individual(name, [15]*16 ) 
        #baseline_calib.char_noise_by_thresh_scan(name,dummy_calib=True)    
        #rigol.output_off(2)
        #Injectors.closeConnection()
        #print(result_matrix)
       # print(x)
        #read threshold_scan from database:
        #dummy_calib = db.get_calib_json_by_name(name,dummy_calib=True)
        #tsbl_scan_raw = dummy_calib["tsbl_scan_raw"]
        #tsbl_range    = dummy_calib["tsbl_range"]
        #print(tsbl_scan_raw)
        #print(tsbl_range)
        tsbl_scan_raw = np.transpose(np.array(result_matrix))
        tsbl_range    = thresholds
        #save to root file 
        #db.dump_db_to_root_board(root_name,name)


    ptc.init_active_boards()  
    gen.set_output_state((1,2),False)
    #Injectors.closeConnection()
    # In[4]:


    #rigol.output_off(2)
    #switch OFF Power supply of PASTTREC board:    
    #htrb.set_state(1,0)

    #import time
    #timestamp = time.time()
    from datetime import datetime
    timestamp = datetime.today().strftime('%Y%m%d%H%M%S')
    # In[5]:
    import matplotlib.backends.backend_pdf
    pdf = matplotlib.backends.backend_pdf.PdfPages(data_output_dicrectory+"/"+"PT_"+serial+"_"+str(timestamp)+"_QA_plots.pdf")


    # staggerd plots:
    fig0 = plt.figure(num=None, figsize=(15, 15), dpi=80, facecolor='w', edgecolor='k')
    #plt.rcParams["figure.figsize"] = (8,9)
    xvals = (np.array(tsbl_range))
    for i in range(0,8):
        
          nums = (np.array(tsbl_scan_raw[i])+1)*10**(8-i)
          print(nums)
          print(xvals)
          plt.plot(xvals,nums,alpha=1,linestyle="dashed")
          plt.scatter(xvals,nums,s=30,alpha=0.4,label = "channel {:d}".format(i))

          plt.legend()
          plt.xlabel("threshold set (LSB)")
          plt.ylabel("mean pulse rate (Hz)")
    plt.yscale('log') 
    plt.ylim(ymax = 1E14, ymin = 0.1)
    #plt.show()
    pdf.savefig(fig0)

    fig0 = plt.figure(num=None, figsize=(15, 15), dpi=80, facecolor='w', edgecolor='k')
    #plt.rcParams["figure.figsize"] = (8,9)
    for i in range(0,8):
         nums = (np.array(noise_scan_raw[i])+1)*10**(8-i)
         plt.plot(noise_range,nums,alpha=1,linestyle="dashed")   
         plt.scatter(noise_range, nums,s=30,alpha=0.4,label = "channel {:d}".format(i))

         plt.legend()
         plt.xlabel("baseline setting (LSB)")
         plt.ylabel("mean pulse rate (Hz)")

    plt.yscale('log') 
    plt.ylim(ymax = 1E16, ymin = 0.1)
    #plt.show()
    pdf.savefig(fig0)

    # In[6]:


    baseline_mean = [] 
    baseline_stdev = [] 
    passed_test =  []   
    
    
    ## Hier TOT messung:

    from TrbDataReader import TrbDataReader
    from PANDAmux import PANDAinjectors
    from PANDAfeb import PANDAfeb

    Injectors = PANDAinjectors()

   # BranchCfg = {}
    #Configure FEB boards connected to the system BranchCfg[testBranch]={"InjAddr":7,"UserID":"B000"}
  #  BranchCfg[0] = {"InjAddr":0,"UserID":"socketTest"}  
    #list of all active branches
    testBranches = list(BranchCfg.keys())
    DataReader = TrbDataReader(testBranches)

    Febs = {}
    for i in testBranches:
        Febs[i] = PANDAfeb(i,BranchCfg[i]["UserID"])
        for qinf in Injectors.InjObjects[BranchCfg[i]["InjAddr"]].qinFactors: 
            Febs[i].convFactors.append(qinf * Injectors.globConvFactor) #conversion factor will be used for all measurements in this sesion and stored with measurements data

    # ---- initializing laboratory equipment ----
    gen = signal_generator("ip:192.168.0.197:5025")
    gen.initialize((1,2))
    gen.set_output_state((1,2),True)

    
    # ---- creating mesurements classes objects ----
    totsMeas = measTOTs(gen,DataReader,Injectors,Febs)
    # ------------------------------------------------------------------------------
    
    #Thresholds = [6, 8, 10, 12, 16, 20]
    Thresholds = [ 20 ]	
    Gains = [ 4  ]	
    ChipConfs = ["{}mV{}ns".format(pt_gain,pt_pktime) ]
    for ConfName in ChipConfs:
        MeasName = "%s"%ConfName
        # -- initial configuration
        #for feb in Febs: Febs[feb].setTypicalConfiguration(ConfName)
        #ptc.init_board_by_name(measure_board_name,pt_pktime ,pt_gain,pt_threshold_default)
        #baselines = baseMeas.getBaselineSettings(MeasName,"Center")
        #printdict(baselines)
        #for feb in Febs: Febs[feb].setBaselines(baselines[feb])
        # -- Threshold Scan ...
        for ga in Gains:		
            ptc.init_board_by_name(measure_board_name,pt_pktime ,ga,pt_threshold_default)
            for th in Thresholds:
                MeasName = "_%sGai%01dTh%03d"%(ConfName,ga,th)
                ptc.set_threshold_for_board_by_name(measure_board_name,th)
                # -- Measurements and fitting
                totsMeas.runTOTsScan(MeasName) #,[0]
                #for feb in Febs: Febs[feb].saveData()  #saving data to files...
                totsMeas.fitTOTsData(MeasName)
                #for feb in Febs: Febs[feb].saveData()  #saving data to files...
                # -- Plotting ...
                figToT = totsMeas.plotTOTsCurves(MeasName)
                #with PdfPages(os.path.join(data_output_dicrectory,"PT_"+serial+MeasName+"_ToT.pdf")) as pdf:
                pdf.savefig(figToT ) #, pad_inches=0.2*cm)
                plt.close(figToT)
    # ------------------------------------------------------------------------------
    # disconnect input switcher injector board
    Injectors.closeConnection()
    #switch OFF Power supply of PASTTREC board:    
    htrb.set_state(1,0)
    # switch off pulse generator
    gen.set_output_state((1,2),False)
    
    
    #baselines plots for each channel:
    print("\n baseline scans")
    plt.rcParams["figure.figsize"] = (8,5)

    def hist_rms(x,y):
      counts = np.sum(y)
      weights = y / counts
      mean = np.dot(x,weights)
      deviations = x - mean
      return np.sqrt(np.dot(deviations**2,weights))
    def MeanArrays(xs,ys):
        return np.dot(xs,ys)/sum(ys)

    for i in range(0,8):
           fig00 = plt.figure(num=None, figsize=(15, 10), dpi=80, facecolor='w', edgecolor='k')
           plt.plot(noise_range,noise_scan_raw[i],alpha=1,linestyle="dashed")
           plt.scatter(noise_range,noise_scan_raw[i],s=30,alpha=1,label = "{:d}".format(i))
           plt.legend()
           plt.xlabel("  baseline setting (LSB) ")
           plt.ylabel("mean pulse rate (Hz)")
           #plt.yscale('log') 
           #plt.show()
           pdf.savefig(fig00)
            
           found_bl_mean = MeanArrays(noise_range,noise_scan_raw[i]) #noise_range[np.array(noise_scan_raw[i]).argmax()]
           found_bl_stdev = hist_rms(noise_range,noise_scan_raw[i])    
           print("found baseline mean = "+ str(found_bl_mean)+ "+- "+ str(found_bl_stdev))
           baseline_mean += [found_bl_mean] 
           baseline_stdev += [found_bl_stdev] 
    

    # In[7]:

    py_noise_halfmax = []
    py_noise_halfmax_err = [] 
    py_noise_sigma = []
    py_noise_sigma_err = []
    py_noise_fit_chi2 = []
    
    # threshold scan fitting s-curve :
    print("\n threshold scans")
    plt.rcParams["figure.figsize"] = (8,6)
    for i in range(0,8): 
        xmin = 7 
        #fit parameters:
        x = np.array(tsbl_range)
        y = np.array(tsbl_scan_raw[i])
        p0 = [np.amax(y),20,1]
        #print(tsbl_scan_raw[i])
        closest = min(y, key=lambda x: abs(x-1.1*freq))
        xmin = x[np.where(y == closest)]
        print(i,closest, xmin)
        #xmin = 7 
        xmax = 50
        #time.sleep(5)
        xmin_fit = max(max(xmin), 10)
        #+ 5*baseline_rms[i]
        try:
            mask = (x >= xmin_fit ) & (x <= xmax)
        except:
            xmin = 10 
            mask = (x >= xmin ) & (x <= xmax)

        xfit = x[mask]
        yfit = y[mask]

        popt = None
        try:
            popt, pcov = curve_fit(sigmoid, xfit, yfit, p0=p0)
            popt, pcov = curve_fit(sigmoid, xfit, yfit, p0=p0)
        except Exception as e:
            print(e)
            popt = [0] * 3
            pcov = [[0 for x in range(3)] for x in range(3)]
            #continue
        
        #plot properties
        maskPlot = (x >= xmin_fit) & (x <= 50)
        x = x[maskPlot]
        y = y[maskPlot]
        
        fig00 = plt.figure(num=None, figsize=(15, 10), dpi=80, facecolor='w', edgecolor='k')
        plt.scatter(x,y,s=30,alpha=1,label = "{:d}".format(i))


        plt.xlabel("threshold LSB ( 2mV / LSB ) ")
        plt.ylabel("mean pulse rate (Hz)")
        #plt.yscale('log')
        errors =  np.sqrt(y) 
        try: 
            TS = calc_chisquare(y, errors , sigmoid(x,*popt))
        except:
            TS = -1
            print ("chi-square not calcable, fit probably failed")
        NDF = len(y) - len(p0)
        print("chisquare/NDF = {0:.2f} / {1:d} = {2:.2f}".format(TS, NDF, TS / NDF))
           
        try:
            plt.plot(x,sigmoid(x,*popt),"r-",label="fit chi2/ndf = {:.2f}".format(TS/NDF))
            plt.title("s-curve channel: "+str(ch))
            #plt.yscale('log')
            plt.legend()
        except:
            print ("fit not plotable probably failed")
        
        perr = np.sqrt(np.diag(pcov))
        
        py_noise_halfmax += [popt[1]]
        py_noise_halfmax_err += [perr[1]] 
        py_noise_sigma += [popt[2]]
        py_noise_sigma_err += [perr[2]] 
        py_noise_fit_chi2 += [ TS / NDF ]
        print(popt)
        print(pcov)
        for p in range(0,len(popt)):
            print("fit pram ",p," = ",popt[p], " +- = ",perr[p])

          # plt.show()
        pdf.savefig(fig00)
    
    
    pdf.close()
  
    
## plots + Auswertung:
    
    totresults = totsMeas.deviationTOTsCurves(MeasName)
    
    # plot fit results for all 8 channels
    #import matplotlib.backends.backend_pdf
    pdf2 = matplotlib.backends.backend_pdf.PdfPages(data_output_dicrectory+"/"+"PT_"+serial+"_QA_results.pdf")


    
    fig1 = plt.figure(num=None, figsize=(20, 6), dpi=80, facecolor='w', edgecolor='k')
    plt.errorbar(range(0,len(baseline_mean)),baseline_mean,baseline_stdev ,xerr=None, alpha=0.5,label = serial)     
    plt.xlabel("channel")
    plt.ylabel("baseline mean position")
    plt.legend()
    plt.ylim(ymax = 16, ymin = -16 )
    #plt.show()
    pdf2.savefig(fig1)

    fig2 = plt.figure(num=None, figsize=(20, 6), dpi=80, facecolor='w', edgecolor='k')
    plt.errorbar(range(0,len(py_noise_halfmax)),py_noise_halfmax,py_noise_halfmax_err ,xerr=None, alpha=0.5,label = serial)     
    plt.xlabel("channel")
    plt.ylabel("half max position of s-curve fit")
    plt.legend()
    plt.ylim(ymax = 25, ymin = 10 )
    #plt.show()
    pdf2.savefig(fig2)

    fig3 = plt.figure(num=None, figsize=(20, 6), dpi=80, facecolor='w', edgecolor='k')
    plt.errorbar(range(0,len(py_noise_sigma)),py_noise_sigma,py_noise_sigma_err ,xerr=None, alpha=0.5,label = serial)     
    plt.xlabel("channel")
    plt.ylabel("sigma of s-curve fit")
    plt.legend()
    plt.ylim(ymax = 2, ymin = 0 )
    #plt.show()
    pdf2.savefig(fig3)

    fig4 = plt.figure(num=None, figsize=(20, 6), dpi=80, facecolor='w', edgecolor='k')
    plt.plot(range(0,len(totresults[4])),totresults[4],marker='o', linestyle="dashed",label = serial)     
    plt.xlabel("channel")
    plt.ylabel("slope of ToT/charge fit [ns/ke-]")
    plt.legend()
    plt.ylim(ymax = 8, ymin = 5 )
    #plt.show()
    pdf2.savefig(fig4)

    fig4 = plt.figure(num=None, figsize=(20, 6), dpi=80, facecolor='w', edgecolor='k')
    plt.plot(range(0,len(totresults[5])),totresults[5],marker='o', linestyle="dashed",label = serial)     
    plt.xlabel("channel")
    plt.ylabel("offset of ToT/charge fit [ns/ke-]")
    plt.legend()
    #plt.ylim(ymax = 8, ymin = 5 )
    #plt.show()
    pdf2.savefig(fig4)    
    
    pdf2.close()
    
    
    #print("Baseline mean [LSB/2mV]: ",baseline_mean,"| mean of 8 channels: ", sum(baseline_mean)/len(baseline_mean), " +- RMS = ", list_rms(baseline_mean) ) 
    #print("S-curve position (maximum half) [LSB/2mV]: ",py_noise_halfmax,"| mean of 8 channels: ", sum(py_noise_halfmax)/len(py_noise_halfmax), " +- RMS = ", list_rms(py_noise_halfmax) )
    #print("S-curve sigma [LSB/2mV]: ",py_noise_sigma,"| mean of 8 channels: ", sum(py_noise_sigma)/len(py_noise_sigma), " +- RMS = ", list_rms(py_noise_sigma) )

    
    
    asic_result = ""        
    for i in range(0,8):
        
        if baseline_mean[i] < 15 and baseline_mean[i] > -15 and py_noise_sigma[i] < 4.0 and py_noise_sigma[i] > 0 and py_noise_halfmax[i] < 20 and py_noise_halfmax[i] > 3  and py_noise_fit_chi2[i] < 200 and totresults[0] < 5 and totresults[1] < 1 and totresults[2] < 1 and totresults[3] < 50:
            passed_test += ['OK']
        elif baseline_mean[i] > 15 or baseline_mean[i] < -15 :
            passed_test += ['no baseline']
            asic_result += "channel {} failed ".format(i)
        elif  py_noise_fit_chi2[i] > 250  and  py_noise_fit_chi2[i] < 0.01 :
            passed_test += ['s-curve fit failed']
            asic_result += "channel {} s-curve failed ".format(i)
        elif  totresults[0] > 10 or totresults[1] > 2   :
            passed_test += ['tot/charge channel deviation high']
            asic_result += "tot/charge channel deviation high"          
        elif  totresults[2] > 1 or totresults[3] > 50   : #RMS of TOT fit parameters:  totresults[2] = RMS of slopes, totresults[3] = RMS of offsets, 
            passed_test += ['tot/charge slope deviation high']
            asic_result += "tot/charge slope deviation high" 
        else    :
            passed_test += ['s-curve or ToT fit out of range']
            asic_result += "channel {} s-curve or ToT out of range ".format(i)
    if not asic_result:
        asic_result = "all channels OK"
    # write results to table over all tested pasttrec as .csv file
    import csv
    #table headers: only uncomment, when file is written for the first time.
   # channel_label_list = ['channel_0', 'channel_1', 'channel_2','channel_3','channel_4' ,'channel_5','channel_6', 'channel_7' ]   
   # l1 = [ "baseline_" + s for s in channel_label_list]
   # l2 = [ "s-curve_halfmax_" + s for s in channel_label_list]
   # l3 = [ "s-curve_sigma_" + s for s in channel_label_list]
   # l4 = [ "s-curve_chi2ndf_" + s for s in channel_label_list]
   # l5 = [ "Test_passed_" + s for s in channel_label_list]
    #table_row = ["serial"] + ["ASIC test result"]+  l1 + l2   + l3  + l4  + l5

    table_row = [serial] + [asic_result] + baseline_mean +  py_noise_halfmax +  py_noise_sigma + py_noise_fit_chi2 + [sum(py_noise_halfmax)/len(py_noise_halfmax)] + [list_rms(py_noise_halfmax)] + [sum(py_noise_sigma)/len(py_noise_sigma)] + [list_rms(py_noise_sigma)] +  passed_test + [totresults[0]] + [totresults[1]] + [totresults[2]] + [totresults[3]] + list( totresults[4]) + list(totresults[5]) 
    with open(data_output_dicrectory+"/PT_results_table.csv", 'a') as f:
            writer = csv.writer(f)
            writer.writerow(table_row)
    #
    
    

    end_time = time.time()
    time_lapsed = end_time - start_time
    time_convert(time_lapsed)
    #time.sleep(30)
    return baseline_mean,  py_noise_halfmax,  py_noise_sigma, py_noise_fit_chi2,  passed_test, totresults, time_lapsed
# In[ ]:




