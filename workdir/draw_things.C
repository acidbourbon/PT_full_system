
#include <iostream>
#include <fstream>

void draw_and_save(TObject *hist,TString name,TString outdir,TString draw_options) {
  
//   if(DRAW_PNG) {
    TCanvas *c = new TCanvas("c_"+name,"c_"+name,200,10,1024,786);
    c->cd();
    hist->Draw(draw_options);
    c->Print(outdir+"/"+name+".png");
//   }
//   c->Print(outdir+name+".pdf");
//     c->Print(outdir+name+".svg");
}

TString from_env(TString env_var,TString default_val){
  if(gSystem->Getenv(env_var)){
    return gSystem->Getenv(env_var);
  } 
  return default_val;
}


void draw_things(TString fname){
  TFile *f = new TFile(fname);
//   f->cd("Histograms/TDC_0353");
  
  TString TDC=from_env("TDC","0351");
  
  
  cout << "contents: "<< endl; 
  f->ls();
  
  
  TString outdir = gSystem->DirName(fname);
  
  
  std::vector<TString> list;
  
  //list.push_back("meta_fish");
//   list.push_back("meta_potato");
  list.push_back("meta_t1_2d");
  list.push_back("meta_tot_2d");
  //list.push_back("coinc_matrix");
//   list.push_back("meta_fish_proj");
//   list.push_back("efficiency");
//   list.push_back("ref_counts");
//   list.push_back("Ch03_t1");
//   list.push_back("Ch03_tot");
//   list.push_back("Ch03_potato");
//   list.push_back("Ch04_t1");
//   list.push_back("Ch04_tot");
//   list.push_back("Ch04_potato");
//   list.push_back("Ch05_t1");
//   list.push_back("Ch05_tot");
//   list.push_back("Ch05_potato");
//   list.push_back("Ch06_t1");
//   list.push_back("Ch06_tot");
//   list.push_back("Ch06_potato");
//   list.push_back("Ch07_t1");
//   list.push_back("Ch07_tot");
//   list.push_back("Ch07_potato");
//   list.push_back("Ch00_potato");
//   list.push_back("Ch07_t1");
//   list.push_back("Ch09_t1");
/*  
  list.push_back("Ch00_t1");
  list.push_back("Ch01_t1");
  list.push_back("Ch02_t1");
  list.push_back("Ch03_t1");
  list.push_back("Ch04_t1");
  list.push_back("Ch05_t1");
  list.push_back("Ch06_t1");
  list.push_back("Ch07_t1");
  

  list.push_back("Ch16_t1");
  list.push_back("Ch17_t1");
  list.push_back("Ch18_t1");
  list.push_back("Ch19_t1");
  list.push_back("Ch20_t1");
  list.push_back("Ch21_t1");
  list.push_back("Ch22_t1");
  list.push_back("Ch23_t1"); */

//   ((TH1F*)f->Get("Histograms/TDC_0353/Ch2/TDC_0353_Ch2_RisingRef"))->Draw()  
  for (Int_t i = 0; i< list.size(); i++){
    draw_and_save(f->Get("Histograms/Sec_"+TDC+"/Sec_"+TDC+"_"+list[i]),list[i],outdir,"colz" );
//     TH1* cumul = ((TH1F*) f->Get("Histograms/Sec_"+TDC+"/Sec_"+TDC+"_"+list[i]))->GetCumulative();
//     draw_and_save(cumul,list[i]+"_cumul",outdir,"colz" );
  }
  
  /*
  TH1F* meta_fish_proj = (TH1F*) f->Get("Histograms/Sec_"+TDC+"/Sec_"+TDC+"_"+"meta_fish_proj");
  //draw_and_save(meta_fish_proj,"meta_fish_proj",outdir,"colz" );
  
  
  gStyle->SetOptFit();
  
  meta_fish_proj->Fit("gaus");
  TF1 *fit = meta_fish_proj->GetFunction("gaus");
  Double_t chi2 = fit->GetChisquare();
  Double_t p2 = fit->GetParameter(2);
  Double_t e2 = fit->GetParError(2);
  cout << "Gauss fit sigma: " << p2 << " +- " << e2 << "ns" << endl;
 
  
  TH1F* efficiency = (TH1F*) f->Get("Histograms/Sec_"+TDC+"/Sec_"+TDC+"_"+"efficiency");
  draw_and_save(efficiency,"efficiency",outdir,"colz text" );
  Float_t avg_efficiency = 0;
  
  // pasttrec average
  
  avg_efficiency += efficiency->GetBinContent(1+4);
  avg_efficiency += efficiency->GetBinContent(1+5);
//     avg_efficiency += efficiency->GetBinContent(1+6); // broken channel
  avg_efficiency += efficiency->GetBinContent(1+7);
  
  avg_efficiency += efficiency->GetBinContent(1+19);
  avg_efficiency += efficiency->GetBinContent(1+20);
  
  avg_efficiency /= 5;
  
  
  
//   // asd8 average
//   avg_efficiency += efficiency->GetBinContent(1+1);
//   avg_efficiency += efficiency->GetBinContent(1+2); 
//   avg_efficiency += efficiency->GetBinContent(1+3);
//   
//   avg_efficiency += efficiency->GetBinContent(1+16);
//   avg_efficiency += efficiency->GetBinContent(1+17);
//   avg_efficiency += efficiency->GetBinContent(1+18);
//   
//   avg_efficiency /= 6;
  
  cout << "avg_efficiency:  " << avg_efficiency << endl;
  
  
  ofstream myfile (outdir + "/" + "results.txt");
  if (myfile.is_open()){
    myfile << "Gauss fit sigma: " << p2 << " +- " << e2 << "ns" << endl;
    myfile << "avg_efficiency:  " << avg_efficiency << endl;
  }
  
  //draw_and_save(meta_fish_proj,"meta_fish_proj_fit",outdir,"colz" );
  
//   new TBrowser();

*/
}

