#!/usr/bin/env python3


##################################################
##     fit scurve to histogram                  ##
##################################################



import ROOT
        
def fit_scurve(raw_scan,startbin = 0.0,chisquare_limit = 1.5): 
    fit_output =  [-1,-1,-1,-1,-1,-1,-1,-1]
    scurve = ROOT.TF1("scurve","[3]+[0]*(1+erf((-1*x+[1])/(sqrt(2)*[2])))",0,130)
    if ( raw_scan.GetEntries() > 100 ):
       c = ROOT.TCanvas("myCanvasName","The Canvas Title",640,480)
       stdev = raw_scan.GetStdDev(1)
       maxX = raw_scan.GetBinCenter(raw_scan.GetMaximumBin()) 
       maxX += startbin      
       scurve.SetParameters(raw_scan.GetMaximum(),stdev,maxX+stdev,raw_scan.GetMaximum()*0.05)
       scurve.SetParLimits(0, raw_scan.GetMaximum()*0.1, raw_scan.GetMaximum()*2);  
       raw_scan.Fit("scurve","Q","",maxX, raw_scan.GetBinCenter(raw_scan.GetNbinsX()))
       c.Draw()
       #c.SaveAs("noiseFit_lay" + str(l) +"_wire" + str(i) +".png")
       function = raw_scan.GetFunction("scurve")
       if (function):
        if(function.GetNDF() > 0 ):
         if( function.GetChisquare()/function.GetNDF() < chisquare_limit):
           fit_output = []
           for ip in range(0,4):
               fit_output += [ function.GetParameter(ip) ]
               fit_output += [ function.GetParError(ip) ]  
    return fit_output


def get_signal_to_noise_distance_tot(htot,tot_noise_threshold):
    
    htot.GetXaxis().SetRangeUser(0,tot_noise_threshold)
    if htot.GetMaximum() < 3 :
        return -1
    noisemax = htot.GetXaxis().GetBinCenter(htot.GetMaximumBin()) 
    htot.GetXaxis().SetRangeUser(tot_noise_threshold,400)
    if htot.GetMaximum() < 3 :
        return -1    
    signalmax = htot.GetXaxis().GetBinCenter(htot.GetMaximumBin()) 
    return (signalmax - noisemax)

def get_signal_to_noise_distance_tot_error(htot,tot_noise_threshold):
    
    htot.GetXaxis().SetRangeUser(0,tot_noise_threshold)
    if htot.GetMaximum() < 3 :
        return 0
    noisemax_stdev = htot.GetStdDev()
    htot.GetXaxis().SetRangeUser(tot_noise_threshold,400)
    if htot.GetMaximum() < 3 :
        return 0    
    signalmax_stdev = htot.GetStdDev()
   
    return (signalmax_stdev + noisemax_stdev)
