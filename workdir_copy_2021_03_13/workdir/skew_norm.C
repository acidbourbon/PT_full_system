
#include <boost/math/distributions/skew_normal.hpp>



Float_t alt_skew_norm(Float_t x, Float_t mean, Float_t stddev, Float_t shape){
  
  if(stddev <0.001)
    stddev=0.001;
  
  if(shape <0.001)
    shape=0.001;
  
  Float_t delta = shape/TMath::Sqrt(1+shape*shape);
  Float_t scale = stddev/TMath::Sqrt(1-2*delta*delta/TMath::Pi());
  Float_t location = mean-scale*delta*TMath::Sqrt(2/TMath::Pi());
  
  boost::math::skew_normal_distribution<Float_t> dist(location,scale,shape);
  return boost::math::pdf(dist,x);
  
}



TArrayF* fit_alt_skewed(TH1* hist){
  TArrayF* return_vals = new TArrayF(7);
  
  Float_t hist_mean = hist->GetMean();
  
/*  
  hist->Fit("gaus","WW");
  TF1 *gausfit = hist->GetFunction("gaus"); */
//   Float_t gauswidth = gausfit->GetParameter(2);
  
  
  TF1 *fit  = new TF1 ("fit","[0]*alt_skew_norm(x,[1],[2],[3])"
                               ,hist_mean-20,hist_mean+20);
  fit->SetParName(0,"const");
  fit->SetParName(1,"fit mean");
  fit->SetParName(2,"fit stddev");
  fit->SetParName(3,"shape");
  fit->SetNpx(1000);
  
  fit->SetParameter(1,hist_mean);
  fit->SetParLimits(1,hist_mean-20,hist_mean+20);
  fit->SetParameter(2,hist->GetStdDev());
  fit->SetParLimits(2,hist->GetStdDev()/2,hist->GetStdDev()*2);
  fit->FixParameter(3,2.2);
  hist->Fit("fit","WW q");
  fit->ReleaseParameter(3);
//   hist->Fit("fit","");
//   hist->Fit("fit","WW M q");
  hist->Fit("fit","M q");
//   hist->Fit("fit","WW M q");
  
  
  
  
  
  Float_t constant = fit->GetParameter(0);
  Float_t fit_mean  = fit->GetParameter(1);
  Float_t fit_stddev = fit->GetParameter(2);
  Float_t shape = fit->GetParameter(3);
  Float_t err_constant = fit->GetParError(0);
  Float_t err_fit_mean  = fit->GetParError(1);
  Float_t err_fit_stddev = fit->GetParError(2);
  Float_t err_shape = fit->GetParError(3);
  
  Float_t delta = shape/TMath::Sqrt(1+shape*shape);
  Float_t scale = fit_stddev/TMath::Sqrt(1-2*delta*delta/TMath::Pi());
  Float_t location = fit_mean-scale*delta*TMath::Sqrt(2/TMath::Pi());
  
//   fit->FixParameter(0,constant);
//   fit->FixParameter(1,fit_mean);
//   fit->FixParameter(2,fit_stddev);
//   fit->FixParameter(3,shape);
//   
//   hist->Fit("fit","");
  
//   Float_t syst_width_error = abs(gauswidth - fit_stddev);
  Float_t syst_width_error = abs(err_fit_stddev);
  
  return_vals->SetAt(constant,0);
  return_vals->SetAt(location,1);
  return_vals->SetAt(scale,2);
  return_vals->SetAt(shape,3);
  
  return_vals->SetAt(fit_mean,4);
  return_vals->SetAt(fit_stddev,5);
  return_vals->SetAt(syst_width_error,6);
  
  
  
  
  return return_vals;
  
}
