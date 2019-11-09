
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
  TH2F* meta_fish_scinti_cut = new TH2F("meta_fish_scinti_cut","meta_fish_scinti_cut", 125, -250, 250, 125, -250, 250);
  
  TH1F* wire_a_t1_scinti_cut = new TH1F("wire_a_t1_scinti_cut","wire_a_t1_scinti_cut", 200, -100, 100);
  TH1F* wire_a_tot_scinti_cut = new TH1F("wire_a_tot_scinti_cut","wire_a_tot_scinti_cut", 900, -100, 800);
  TH1F* wire_b_t1_scinti_cut = new TH1F("wire_b_t1_scinti_cut","wire_b_t1_scinti_cut", 200, -100, 100);
  TH1F* wire_b_tot_scinti_cut = new TH1F("wire_b_tot_scinti_cut","wire_b_tot_scinti_cut", 900, -100, 800);
  
  TH1F* scinti_t1_scinti_cut = new TH1F("scinti_t1_scinti_cut","scinti_t1_scinti_cut", 200, -100, 100);
  TH1F* scinti_tot_scinti_cut = new TH1F("scinti_tot_scinti_cut","scinti_tot_scinti_cut", 900, -100, 800);
  TH1F* scinti_t1 = new TH1F("scinti_t1","scinti_t1", 200, -100, 100);
  TH1F* scinti_tot = new TH1F("scinti_tot","scinti_tot", 900, -100, 800);
  

  for (Int_t evt_no = 0; evt_no < joint_tree->GetEntries(); evt_no++){

    joint_tree->GetEntry(evt_no);
    
    Float_t wire_a_t1_candidate  = -1000;
    Float_t wire_b_t1_candidate  = -1000;
    Float_t wire_a_tot_candidate = -1000;
    Float_t wire_b_tot_candidate = -1000;
    Float_t my_scinti_t1 = -1000;
    Float_t my_scinti_tot = -1000;

    for (Int_t hit_no_a = 0; hit_no_a < this_event->hits.size(); hit_no_a++){
      Int_t hit_a_chan = this_event->hits[hit_no_a].chan;
      Int_t hit_a_wire = this_event->hits[hit_no_a].wire;
      
      if (         this_event->hits[hit_no_a].chamber == chamber_a &&
                   this_event->hits[hit_no_a].layer == layer_a && 
                   this_event->hits[hit_no_a].wire == wire_a     ){
         // we have wire a hit
        wire_a_t1_candidate  = this_event->hits[hit_no_a].t1;
        wire_a_tot_candidate = this_event->hits[hit_no_a].tot;
      }
      if (         this_event->hits[hit_no_a].chamber == chamber_b &&
                   this_event->hits[hit_no_a].layer == layer_b && 
                   this_event->hits[hit_no_a].wire == wire_b     ){
         // we have wire b hit
        wire_b_t1_candidate  = this_event->hits[hit_no_a].t1;
        wire_b_tot_candidate = this_event->hits[hit_no_a].tot;
      }
      
      
      
      
      if (  this_event->hits[hit_no_a].chan == scinti_chan ){
        my_scinti_t1   = this_event->hits[hit_no_a].t1;
        my_scinti_tot  = this_event->hits[hit_no_a].tot;
      }
        
      
      for (Int_t hit_no_b = hit_no_a; hit_no_b < this_event->hits.size(); hit_no_b++){
        Int_t hit_b_chan = this_event->hits[hit_no_b].chan;
        Int_t hit_b_wire = this_event->hits[hit_no_b].wire;

          coinc_matrix->Fill(hit_a_chan,hit_b_chan);
//           if(hit_a_wire &&  hit_b_wire ){
             Float_t t1_a = this_event->hits[hit_no_a].t1;
             Float_t t1_b = this_event->hits[hit_no_b].t1;
             meta_fish->Fill(t1_a +t1_b, t1_a -t1_b);	
                
             if(this_event->hits[hit_no_a].t1 > t1_L && this_event->hits[hit_no_b].t1 > t1_L) {
    
               if(this_event->hits[hit_no_a].layer == this_event->hits[hit_no_b].layer) {
                 // do not correlate stuff from the same layer
               } else if(
                   this_event->hits[hit_no_a].chamber == chamber_a &&  this_event->hits[hit_no_b].chamber == chamber_b  &&
                   this_event->hits[hit_no_a].layer == layer_a     &&  this_event->hits[hit_no_b].layer == layer_b  &&
                   this_event->hits[hit_no_a].wire == wire_a     &&  this_event->hits[hit_no_b].wire == wire_b                    
                        ){  
                   if(this_event->hits[hit_no_a].tot >tot_L && this_event->hits[hit_no_a].tot < tot_R ){
                    if(this_event->hits[hit_no_b].tot >tot_L && this_event->hits[hit_no_b].tot < tot_R ){
                     coinc_matrix_wire_cut->Fill(hit_a_wire,hit_b_wire);

                     // this_event->hits[hit_no_a].t1
                     // so kriegst du auch andere Groessen (chan, trig_no, tot, wire, layer, fpc, chamber ...)

                     meta_fish_cut->Fill(t1_a +t1_b, t1_a -t1_b);
                    }
                   } else coinc_matrix_wire->Fill(hit_a_wire,hit_b_wire);
               }
             } 
//         }

      }
    }
    
    /////////////   filling the cleaned histos
    if (my_scinti_t1 > -1000){
      scinti_t1->Fill(my_scinti_t1);
      scinti_tot->Fill(my_scinti_tot);
    }
    if (my_scinti_t1 > scinti_cut_L && my_scinti_t1 < scinti_cut_R){
      scinti_t1_scinti_cut->Fill(my_scinti_t1);
      scinti_tot_scinti_cut->Fill(my_scinti_tot);
      
      if (wire_a_t1_candidate > -1000 ){
        wire_a_t1_scinti_cut->Fill(wire_a_t1_candidate);
        wire_a_tot_scinti_cut->Fill(wire_a_tot_candidate);
      }
      if (wire_b_t1_candidate > -1000 ){
        wire_b_t1_scinti_cut->Fill(wire_b_t1_candidate);
        wire_b_tot_scinti_cut->Fill(wire_b_tot_candidate);
      }
      if (wire_a_t1_candidate > -1000  && wire_b_t1_candidate > -1000 ){
        meta_fish_scinti_cut->Fill(wire_a_t1_candidate + wire_b_t1_candidate, wire_a_t1_candidate - wire_b_t1_candidate );
      }
    }
    
    

  }
  
  out_file->Write();
//~ 
TCanvas * can_conic = new TCanvas("can_conic","can_conic",1000,600);
// can_conic->Divide(2,1);
// can_conic->cd(1);
// coinc_matrix_wire->Draw("colz");
// //~ meta_fish->Draw("colz");
// can_conic->cd(2);
// coinc_matrix_wire_cut->Draw("colz");
  meta_fish_cut->Draw("colz");
}
