
#include "correlation.h"

class Hit {
public:
  int chan;
  int trig_no;
  int ref_chan;
  double t1;
  double tot;
  int wire;
  int layer;
  int fpc;
  int chamber;
};

class Event {
public:
  std::vector<Hit> hits;
};


TString from_env(TString env_var,TString default_val){
  if(gSystem->Getenv(env_var)){
    return gSystem->Getenv(env_var);
  } 
  return default_val;
}

Float_t from_env_float(TString env_var,TString default_val){
  TString val = default_val;
  if(gSystem->Getenv(env_var)){
    val = gSystem->Getenv(env_var);
  } 
  return val.Atof();
}

Int_t from_env_int(TString env_var,TString default_val){
  TString val = default_val;
  if(gSystem->Getenv(env_var)){
    val = gSystem->Getenv(env_var);
  } 
  return val.Atoi();
}



void correlation(void){
    
  TString in_file_name = from_env("in_file","./joint_tree.root");
    
  TFile* in_file = new TFile(in_file_name);
   
  TTree* joint_tree = (TTree* ) in_file->Get("joint_tree");
 //joint_tree = (TTree* ) gDirectory->Get("joint_tree");
  Event* this_event = new Event();
  joint_tree->SetBranchAddress("event",&this_event);
  
  TFile* out_file = new TFile("./correlation.root","RECREATE");
  out_file->cd();

  TH2F* coinc_matrix = new TH2F("coinc_matrix","coinc_matrix", 500, 35000, 35000+500, 500, 35000, 35000+500);
  TH2F* coinc_matrix_wire = new TH2F("coinc_matrix_wire","coinc_matrix_wire", 200, 0, 200, 200, 0, 200);
  TH2F* coinc_matrix_wire_cut = new TH2F("coinc_matrix_wire_cut","coinc_matrix_wire_cut", 200, 0, 200, 200, 0, 200);

  TH2F* meta_fish = new TH2F("meta_fish","meta_fish", 125, -250, 250, 125, -250, 250);
  TH2F* meta_fish_cut = new TH2F("meta_fish_cut","meta_fish_cut", 125, -250, 250, 125, -250, 250);

  for (Int_t evt_no = 0; evt_no < joint_tree->GetEntries(); evt_no++){

    joint_tree->GetEntry(evt_no);

    for (Int_t hit_no_a = 0; hit_no_a < this_event->hits.size(); hit_no_a++){
      Int_t hit_a_chan = this_event->hits[hit_no_a].chan;
      Int_t hit_a_wire = this_event->hits[hit_no_a].wire;
      for (Int_t hit_no_b = hit_no_a; hit_no_b < this_event->hits.size(); hit_no_b++){
        Int_t hit_b_chan = this_event->hits[hit_no_b].chan;
        Int_t hit_b_wire = this_event->hits[hit_no_b].wire;

          coinc_matrix->Fill(hit_a_chan,hit_b_chan);
          if(hit_a_wire &&  hit_b_wire ){
             Float_t t1_a = this_event->hits[hit_no_a].t1;
             Float_t t1_b = this_event->hits[hit_no_b].t1;
             meta_fish->Fill(t1_a +t1_b, t1_a -t1_b);	
                
             if(this_event->hits[hit_no_a].t1 < t1_L && this_event->hits[hit_no_b].t1 < t1_L) {
    
               if(this_event->hits[hit_no_a].layer == this_event->hits[hit_no_b].layer) {
                 // do not correlate stuff from the same layer
               } else if( this_event->hits[hit_no_a].chamber ==  this_event->hits[hit_no_b].chamber ){   // same chamber!
                   if(this_event->hits[hit_no_a].tot >100 && this_event->hits[hit_no_a].tot < 250 ){
                     coinc_matrix_wire_cut->Fill(hit_a_wire,hit_b_wire);

                     // this_event->hits[hit_no_a].t1
                     // so kriegst du auch andere Groessen (chan, trig_no, tot, wire, layer, fpc, chamber ...)

                     meta_fish_cut->Fill(t1_a +t1_b, t1_a -t1_b);
                   } else coinc_matrix_wire->Fill(hit_a_wire,hit_b_wire);
               }
             } 
        }

      }
    }

  }
  
  out_file->Write();
//~ 
TCanvas * can_conic = new TCanvas("can_conic","can_conic",1000,600);
can_conic->Divide(2,1);
can_conic->cd(1);
coinc_matrix_wire->Draw("colz");
//~ meta_fish->Draw("colz");
can_conic->cd(2);
coinc_matrix_wire_cut->Draw("colz");
//~ meta_fish_cut->Draw("colz");
}
