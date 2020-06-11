#!/usr/bin/env python3


##################################################
##     fit scurve to histogram                  ##
##################################################



import ROOT
        
def fit_scurve(raw_scan): 
    fit_output =  [-1,-1,-1,-1,-1,-1]
    scurve = ROOT.TF1("scurve","[0]*(1+erf((-1*x+[1])/(sqrt(2)*[2])))",0,80)
    if ( raw_scan.GetEntries() > 100 ):
       c = ROOT.TCanvas("myCanvasName","The Canvas Title",640,480)
       stdev = raw_scan.GetStdDev(1)
       maxX = raw_scan.GetBinCenter(raw_scan.GetMaximumBin()) 
       maxX -= 1.0       
       scurve.SetParameters(raw_scan.GetMaximum(),stdev,maxX+stdev)
       raw_scan.Fit("scurve","Q","",maxX, raw_scan.GetBinCenter(raw_scan.GetNbinsX()))
       c.Draw()
       #c.SaveAs("noiseFit_lay" + str(l) +"_wire" + str(i) +".png")

       function = raw_scan.GetFunction("scurve")
       if (function.GetChisquare() < 400):
           fit_output = []
           for ip in range(0,3):
               fit_output += [ function.GetParameter(ip) ]
               fit_output += [ function.GetParError(ip) ]  
    return fit_output
