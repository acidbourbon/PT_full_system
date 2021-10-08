#include <stdio.h>
#include <iostream>
#include <fstream>
#include <map>

#include "TTree.h"
#include "TFile.h"
#include "TSystem.h"
#include "TString.h"
#include "TH1.h"
#include "TH2.h"
#include "TCanvas.h"
#include "TGo4AnalysisObjectManager.h"


#include "base/EventProc.h"
#include "base/Event.h"
#include "hadaq/TdcSubEvent.h"

#include "go4_settings.h"

// #define CHANNELS 53 // in "go_settings.h"
#define REFCHAN 0
// #define REFCHAN_B 0

#define VERBOSE 0
#define TAKE_FIRST_HIT 1



// Muentz-Torte
// #define t1_L -800 // EE
// #define t1_R 800 // EE
// #define tot_L -10 // EE
// #define tot_R 2000 // EE

//#define ref_channel_offset -75 //ns fine measured ref channel relative to coarse measured cts trigger channel
#define ref_channel_offset 0 //ns fine measured ref channel relative to coarse measured cts trigger channel

// in the first iteration, scanning through data in the coincidence window, rejecting hits (fuzzy edges)


// moved to "go4_settings.h"
// #define spike_rejection 80 // for PASTTREC test
// #define spike_rejection_refchan 10

#define individual_spike_rejection 0



#define t1_accept_L ( t1_L + ref_channel_offset) //ns // EE
#define t1_accept_R ( t1_R + ref_channel_offset) //ns // EE

#define fish_proj_cut 20



// real cuts on selected data

#define max_tot 1000000 // Muentz-Torte
#define t1_cut_L -4000
#define t1_cut_R 4000


// #define coincidence_rejection 7
#define accept_hits_per_layer 2000

#define enable_coincidence_rejection 0

#define enable_single_hits       0
#define enable_one_hit_per_layer 1
#define enable_two_to_one_hits   0



// TFile* tree_out;
std::map<std::string,int> trig_no;
std::map<std::string,TTree*> data_tree;
Bool_t write_tree = false;



Bool_t file_exists(TString fname){
  
  fstream src_file(fname.Data());
  return src_file.good();
}

TString from_env(TString env_var,TString default_val){
  if(gSystem->Getenv(env_var)){
    return gSystem->Getenv(env_var);
  } 
  return default_val;
}



class SecondProc : public base::EventProc {
   protected:

      std::string fTdcId;      //!< tdc id where channels will be selected

      double      fHits[8];    //!< 8 channel, abstract hits

      base::H1handle  hNumHits; //!< histogram with hits number
//       base::H2handle  h2D;
      
//       base::H1handle  totCh1; //!< histogram with hits number
//       base::H1handle  totCh2; //!< histogram with hits number
      
      base::H1handle  meta_potato_h;
      base::H1handle  meta_t1_h;
      base::H1handle  meta_tot_h;
      base::H1handle  meta_tot_2d;
      base::H1handle  meta_t1_2d;
            
      base::H1handle  tot_h[CHANNELS+1]; 
      base::H1handle  tot_untrig_h[CHANNELS+1]; 
      base::H1handle  t1_untrig_h[CHANNELS+1]; 
      base::H1handle  t2_untrig_h[CHANNELS+1]; 
      base::H1handle  t1_h[CHANNELS+1]; 
      base::H1handle  potato_h[CHANNELS+1];

      base::H1handle  coinc_matrix;
//      base::H1handle  meta_fish;
//      base::H1handle  meta_fish_proj;
//      base::H1handle  fishes[FISHES];
//      base::H1handle  fish_proj[FISHES];
      base::H1handle  efficiency_h;
      base::H1handle  ref_counts_h;
      base::H1handle  dut_counts_h;
      
      
      int entry_chan;
      int entry_ref_chan;
      double entry_t1;
      double entry_tot;
      
      
      
      
      
//       int evt_no;
      
   public:
      SecondProc(const char* procname, const char* _tdcid) :
         base::EventProc(procname),
         fTdcId(_tdcid),
         hNumHits(0)
      {
         printf("Create %s for %s\n", GetName(), fTdcId.c_str());

         hNumHits = MakeH1("FineAll","Fine all", 1020, 0, 1020, "fine");
//          h2D = MakeH2("h2d","title", 100, -20, 20, 100, -20,20,"x;y");
//          totCh1 = MakeH1("totCh1","totCh1", 20000, -200, 200, "ns");
//          totCh2 = MakeH1("totCh2","totCh2", 20000, -200, 200, "ns");
         
         
       if(from_env("tree_out","false") == "true"){
         write_tree = true;
       }
         
       trig_no[fTdcId] = 0;  
       data_tree[fTdcId] = new TTree((TString) fTdcId,"data recorded");
       data_tree[fTdcId]->Branch("trig_no",&trig_no[fTdcId]);
       data_tree[fTdcId]->Branch("t1",&entry_t1);
       data_tree[fTdcId]->Branch("tot",&entry_tot);
       data_tree[fTdcId]->Branch("chan",&entry_chan);
       data_tree[fTdcId]->Branch("ref_chan",&entry_ref_chan);
       
        meta_t1_h = MakeH1("meta_t1","meta_t1", 2000, t1_L, t1_R, "ns");
        meta_t1_2d = MakeH2("meta_t1_2d","meta_t1_2d", 2000, t1_L, t1_R,CHANNELS-1,0.5,CHANNELS-0.5, "ns;channel#");
        meta_tot_h = MakeH1("meta_tot","meta_tot", 4000, tot_L, tot_R, "ns");
        meta_tot_2d = MakeH2("meta_tot_2d","meta_tot_2d", 2000, tot_L, tot_R,CHANNELS-1,0.5,CHANNELS-0.5, "ns;channel#");
        meta_potato_h = MakeH2("meta_potato","meta_potato",500,t1_L,t1_R,500, tot_L, tot_R, "t1 (ns);tot (ns)");
         ((TObject*) meta_t1_2d)->SetDrawOption("colz");
         ((TH2F*) meta_tot_2d)->SetDrawOption("COLZ");
         ((TObject*) meta_potato_h)->SetDrawOption("colz");       
        for( unsigned i=0; i<CHANNELS+1; i++ ) {
          char chno[16];
          sprintf(chno,"Ch%02d_t1",i);
          t1_h[i] = MakeH1(chno,chno, 1000, t1_L, t1_R, "ns");
          sprintf(chno,"Ch%02d_tot",i);
          tot_h[i] = MakeH1(chno,chno, 1000, tot_L, tot_R, "ns");
          sprintf(chno,"Ch%02d_tot_untrig",i);
          tot_untrig_h[i] = MakeH1(chno,chno, 4000, tot_L, tot_R, "ns");
          sprintf(chno,"Ch%02d_t1_untrig",i);
          t1_untrig_h[i] = MakeH1(chno,chno, 4000, t1_L, t1_R, "ns");
          sprintf(chno,"Ch%02d_t2_untrig",i);
          t2_untrig_h[i] = MakeH1(chno,chno, 4000, t1_L, t1_R, "ns");
          sprintf(chno,"Ch%02d_potato",i);
          potato_h[i] = MakeH2(chno,chno,500,t1_L,t1_R,500, tot_L, tot_R, "t1 (ns);tot (ns)");
        }
        

        efficiency_h = MakeH1("efficiency","efficiency", CHANNELS -1, 0.5, CHANNELS-0.5, "channel #;kind:F");
            ((TH1F*) efficiency_h)->SetDrawOption("P0");
            ((TH1F*) efficiency_h)->SetMarkerStyle(22);
            ((TH1F*) efficiency_h)->GetXaxis()->SetNdivisions(55);
         
        //coinc_matrix = MakeH2("coinc_matrix","coinc_matrix",12,-2.5,9.5,10,15-0.5,24+0.5, "channels 0-7;channels 16-23");
         coinc_matrix = MakeH2("coinc_matrix","coinc_matrix",12,-0.5,11.5,12,-0.5,11.5, "channels 0-10;channels 0-10");
         
         // enable storing already in constructor
         SetStoreEnabled();
      }
      
      virtual void UserPostLoop(void) {
        
        static Int_t was_called_before = 0;
        
        cout << "--- User Post Loop " << fTdcId << endl;
        
        if(from_env("tree_out","false") == "true"){
          
          cout << "write tree_out.root" << endl;
          TFile* tree_out;
          
          
          if(was_called_before){
            tree_out = new TFile("tree_out.root","UPDATE");
          } else {
            tree_out = new TFile("tree_out.root","RECREATE");
          }
          tree_out->cd();
          data_tree[fTdcId]->Write();
          tree_out->Write();
          tree_out->Close();
          delete tree_out;
        }
        was_called_before ++;
      }


      virtual void CreateBranch(TTree* t)
      {
         // only called when tree is created in first.C
         // one can ignore
         t->Branch(GetName(), fHits, "hits[8]/D");
      }

      virtual bool Process(base::Event* ev)
      {
//          printf("### DEBUG ###\n");
         for (unsigned n=0;n<8;n++) fHits[n] = 0.;

         hadaq::TdcSubEvent* sub =
               dynamic_cast<hadaq::TdcSubEvent*> (ev->GetSubEvent(fTdcId));
         
         if(VERBOSE) cout<< "tdc: " << fTdcId << " evt no: " << trig_no[fTdcId] << endl;
         if (sub==0) return false;

//         printf("%s process sub %d %s\n", GetName(), sub->Size(), fTdcId.c_str());

        
        static float effective_spike_rejection = from_env("spike_rejection", TString::Itoa(spike_rejection,10) ).Atof();
        
        
        
        

         double num(0), ch0tm(0), ch1tm(0), ch2tm(0), ch3tm(0);
         double t1_candidate[CHANNELS];
         double t2_candidate[CHANNELS];
         double t1[CHANNELS];
         double t2[CHANNELS];
         bool   got_rising[CHANNELS];
         bool   got_falling[CHANNELS];
         bool   got_real_hit[CHANNELS];
         double tot[CHANNELS];
         for (unsigned i=0; i<CHANNELS; i++) {
           got_rising[i] = false;
           got_falling[i] = false;
           got_real_hit[i] = false;
         }
         

         for (unsigned cnt=0;cnt<sub->Size();cnt++) {
            const hadaq::TdcMessageExt& ext = sub->msg(cnt);

            unsigned chid = ( ext.msg().getHitChannel()  );
           bool rising   = ext.msg().isHitRisingEdge(); // use this line for rising edge first/positive pulses
            
            if (chid==0) {
              ch0tm = ext.GetGlobalTime();
              got_real_hit[chid] = true;
              t1[chid] = 0;
              tot[chid] = 100e-9;
              continue;
              
            }
            

            // full time
            double tm = ext.GetGlobalTime();
            if((chid) >= CHANNELS) {continue;} // channel out of range of analysis
            if(rising){
              
              
              if( !(TAKE_FIRST_HIT && got_real_hit[chid]) ){ // block subsequent hits if TAKE_FIRST_HIT setting is active
                if((( ((tm)*1e9) > t1_accept_L) && (((tm)*1e9) < t1_accept_R ))  ) { // this condition sets another coincidence window, except for REFCHAN_A
                  got_rising[chid] = true;
                  got_falling[chid] = false;
                  t1_candidate[chid] = tm;
                }
              }
            }else{ // if falling edge
//               printf("got falling edge, ch %d\n",(chid));
              if(got_rising[chid]){
                if(not(got_falling[chid])){
                  got_falling[chid] = true;
                  t2_candidate[chid] = tm;
                  Double_t candidate_tot_ns = (t2_candidate[chid] - t1_candidate[chid])*1e9;
                  
                  if( candidate_tot_ns > effective_spike_rejection || (chid==REFCHAN && candidate_tot_ns > spike_rejection_refchan) ){
                    // hit is long enough not to be rejected
                    t1[chid] = t1_candidate[chid];
                    t2[chid] = t2_candidate[chid];
                    tot[chid] = t2[chid] - t1[chid];
                    got_real_hit[chid] = true;
                    
                    // fill untriggered tot histogram
                    FillH1(tot_untrig_h[chid],tot[chid]*1e9);
                    FillH1(t1_untrig_h[chid],t1[chid]*1e9);
                    FillH1(t2_untrig_h[chid],t2[chid]*1e9);
                    FillH1(tot_untrig_h[CHANNELS],tot[chid]*1e9);
                    FillH1(t1_untrig_h[CHANNELS],t1[chid]*1e9);
                    if(tot[chid]>50/1e9) {
						FillH1(t2_untrig_h[CHANNELS],t2[chid]*1e9);
					}
                  }
//                   printf("got hit, ch %d, tot = %f ns\n",(chid), tot[chid]*1e9);
                }
              }
            }
            
         }
         
         
         
         for( unsigned i=0; i<CHANNELS; i++ ) {
            if(got_real_hit[i]){
              
//               if(got_real_hit[REFCHAN_A] || got_real_hit[REFCHAN_B] || REFCHAN_A == -1 || REFCHAN_B == -1){ // t1 information only makes sense if you have 
                // a hit in the reference channel
                double t1_vs_ref = (t1[i] -t1[REFCHAN])*1e9 ;
                if( (t1_vs_ref > t1_cut_L) && (t1_vs_ref < t1_cut_R) && (tot[i]*1e9 < max_tot) )  {
                  
                  // fill histograms
                  FillH1(tot_h[i],tot[i]*1e9);
                  FillH2(potato_h[i],t1_vs_ref ,tot[i]*1e9); 
                  FillH2(potato_h[CHANNELS],t1_vs_ref ,tot[i]*1e9); 
                  FillH1(t1_h[i],t1_vs_ref ); // without cuts
//                  if(t1_vs_ref < -200 && tot[i]*1e9 > 0 )	FillH1(t1_h[i],t1_vs_ref ); // with noise rejecting cuts
		// if(  tot[i]*1e9 > 50 ) 	FillH1(t1_h[i],t1_vs_ref ); // with noise rejecting cuts
 
                  
                  if( i != 0 ) {
                    FillH2(meta_potato_h,t1_vs_ref,tot[i]*1e9);
                    FillH1(meta_tot_h,tot[i]*1e9);
                    FillH1(meta_t1_h,t1_vs_ref );
                    FillH2(meta_tot_2d,tot[i]*1e9,i);
                    FillH2(meta_t1_2d,t1_vs_ref,i);
                    entry_chan = i;
                    entry_t1 = t1_vs_ref;
                    entry_tot = tot[i]*1e9;
                    if(write_tree){
                      data_tree[fTdcId]->Fill();
                    }
                  }
                  
                  // efficiency estimation ... this cell, cell #i, is a reference detector
//                   ref_counts[i]++; // count up reference counts
//                   FillH1(counts_h,i-0.5);
                }
            }
         }
         
 
        
        for (int i = 1 ; i<CHANNELS; i++) {
      //  ((TH1F*) efficiency_h)->SetBinContent(i,((float) (((TH1F*) t1_h[i])->GetEntries()) )/((float) (((TH1F*) t1_h[0])->GetEntries())));
          ((TH1F*) efficiency_h)->SetBinContent(i,((float) (((TH1F*) t1_h[i])->Integral()) )/ 600. ); // fixed numer of pulses sent for each channel 
       //   ((TH1F*) efficiency_h)->SetBinContent(i,((float) (((TH1F*) t1_h[i])->Integral()) )/((float) (((TH1F*) tot_h[i])->Integral())));   ; // normalize by number of signals in same channel without couts, as for almost each trigger a noise signal is measured
        }
        
        
        
         
//          if(got_real_hit[0]){
//           FillH1(totCh1,tot[0]*1e9);
//          }
//          if(got_real_hit[1]){
//           FillH1(totCh2,tot[1]*1e9);ref_counts[i]
//          }

//         FillH1(hNumHits, num);


//          draw_and_save((TH2F*) meta_fish, "meta_fish","./","colz");

//    tree_out->cd();
//    data_tree[fTdcId]->Write();
         trig_no[fTdcId]++;
         
         return true;
      }
      
      
};


void second()
{
   //hadaq::TdcProcessor::SetDefaults(700);
//    tree_out = new TFile("./tree_out.root","RECREATE");
//    new SecondProc("Sec_1130", "TDC_1130");
//   new SecondProc("Sec_0352", "TDC_0353");
//  new SecondProc("Sec_0350", "TDC_0350");
//  new SecondProc("Sec_0351", "TDC_0351");
//  new SecondProc("Sec_0352", "TDC_0352");
//  new SecondProc("Sec_0353", "TDC_0353");
//
//  new SecondProc("Sec_1500", "TDC_1500");
//  new SecondProc("Sec_1501", "TDC_1501");
//  new SecondProc("Sec_1502", "TDC_1502");
//  new SecondProc("Sec_1503", "TDC_1503");
//   tree_out->Write();
//   tree_out->Close();
   
  SECOND_PROCESS_TDCs


}

