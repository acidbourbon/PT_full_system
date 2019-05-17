


#include "Riostream.h"

#define NO_TDCS 16
#define MAX_CHANNELS 64

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


void get_channel_info(TString TDC,Float_t* t1_offsets, Int_t* chamber, Int_t* layer, Int_t* fpc, Int_t* wire){
  

  TString fname = "unify_channel_info/"+TDC + ".channel_info.txt";

      ifstream in;
      in.open(fname);
  
      cout << "read t1 offsets of " << TDC << endl;
  
      Int_t nlines = 0;
      cout << " " << endl;
      
      string line;
      while (getline(in,line)) {
        
        Float_t x1;
        Int_t x2,x3,x4,x5;
        if(sscanf(line.c_str(),"%f %d %d %d %d",&x1,&x2,&x3,&x4,&x5)){
          t1_offsets[nlines] = x1;
          chamber[nlines]    = x2;
          layer[nlines]      = x3;
          fpc[nlines]        = x4;
          wire[nlines]       = x5;
          nlines++;
          cout << "line: " << line.c_str() << endl;
          cout << "chan " << nlines << " t1_offset " << x1 << " chamber " << x2 << " layer " << x3 << " fpc " << x4 << " wire " << x5 << endl;
        }
      }

}


void unify(void){
  
  Int_t correct_t1_offsets = 1;

  Float_t global_t1_shift = 260.0;

  cout << "get t1 offsets from database" << endl;

  gSystem->GetFromPipe("./create_channel_info.py");

  cout << gSystem->GetFromPipe("ls unify_channel_info/*.channel_info.txt") << endl;
  
  cout << "unify!" <<endl;
  
  Int_t channels = 32;
  
  Int_t ref_chan = 35301; // channel 1 of FPGA 0x0351 is our reference channel!
  //Int_t ref_chan = 35049; // channel 49 of FPGA 0x0350 is our reference channel!
  
  
  TFile f("tree_out.root");
  TIter next(f.GetListOfKeys());
   
   
  std::vector<TString> TDC_list;

  
   
   TKey *key;
   while ((key=(TKey*)next())) {
//       printf("key: %s points to an object of class: %s at \n",
//       key->GetName(),
//       key->GetClassName());
//       key->GetClassName(),key->GetSeekKey());
      TDC_list.push_back(key->GetName());
   }
  
  Float_t t1_offsets[NO_TDCS][MAX_CHANNELS];
  Int_t   wire_info[NO_TDCS][MAX_CHANNELS];
  Int_t   fpc_info[NO_TDCS][MAX_CHANNELS];
  Int_t   layer_info[NO_TDCS][MAX_CHANNELS];
  Int_t   chamber_info[NO_TDCS][MAX_CHANNELS];
   
  TTree* data_tree[TDC_list.size()];
  Int_t  channel_number_prefix[TDC_list.size()];
  Int_t data_tree_entries[TDC_list.size()];
  Int_t data_tree_index[TDC_list.size()];
  
  
  
  Hit current_hit;
  
  
  
  ////////////////// make sure you always write into current hit!!! ////////////////
  
  for (Int_t i = 0; i < TDC_list.size(); i++){
    
    TString tdc(TDC_list[i]);

    
    cout << "found data tree for tdc: " << tdc << endl;
    
    TString tdc_hex(tdc);
    tdc_hex.ReplaceAll("TDC_","0x");
    cout << "get t1 offsets for tdc: " << tdc_hex << endl;
    
    //if(correct_t1_offsets)
    get_channel_info(tdc_hex,t1_offsets[i],chamber_info[i],layer_info[i],fpc_info[i],wire_info[i]);
    
    
    TString tdc_number_str( tdc(4,7) );
    Int_t   tdc_number = tdc_number_str.Atoi();
//     cout << "TDC number: " <<  tdc_number <<  endl;
    cout << "TDC channel prefix/offset (100 possible TDC channels left): " <<  tdc_number*100 <<  endl;
    
    data_tree[i] = (TTree*) f.Get(tdc);
    channel_number_prefix[i] = tdc_number*100;
    
    data_tree_entries[i] = data_tree[i]->GetEntries();
    
    data_tree_index[i] = 0;
//     data_tree_end_reached[i] = false;
    cout << "    tree: " << TDC_list[i] << " entries: " << data_tree[i]->GetEntries() << endl;
    
    data_tree[i]->SetBranchAddress("trig_no", &current_hit.trig_no);
    data_tree[i]->SetBranchAddress("t1",      &current_hit.t1);
    data_tree[i]->SetBranchAddress("tot",     &current_hit.tot);
    data_tree[i]->SetBranchAddress("chan",    &current_hit.chan);
    data_tree[i]->SetBranchAddress("ref_chan",&current_hit.ref_chan);
    cout << endl;
    cout << endl;
  }
  
  //////////////////// slurp/combine GO4 data /////////////////////
  
  
  TFile* out_file = new TFile("joint_tree.root","RECREATE");
  
  out_file->cd();
  TTree* joint_tree = new TTree("joint_tree","joint_tree");
//   std::vector<Hit> hit_list;
  
  Event my_event;
  joint_tree->Branch("event",&my_event);
  
  for (Int_t trig_no = 0; trig_no < 10000000 || true; trig_no++){
    
    Bool_t all_ends_reached = true; 
    Int_t hits_per_trigger = 0;
    
    // loop over all participating TDCs
    
    Float_t reference_time = 0;
    Bool_t  got_reference_time = false;
    
    my_event.hits.clear();
    
    for (Int_t tdc_no = 0; tdc_no < TDC_list.size(); tdc_no ++){
      
      // loop over tree entries
      while ( data_tree_index[tdc_no] < data_tree_entries[tdc_no] ) {
        all_ends_reached = false;
        data_tree[tdc_no]->GetEntry(data_tree_index[tdc_no]);
        
        if (current_hit.trig_no == trig_no){
            hits_per_trigger++;
            // here the interesting stuff happens, do something with the
            // current hit

            // correct t1 offsets of TDC
            if(correct_t1_offsets)
              current_hit.t1 -= t1_offsets[tdc_no][current_hit.chan-1];

            // enter database info into the tree
            current_hit.wire     = wire_info[tdc_no][current_hit.chan-1];
            current_hit.chamber  = chamber_info[tdc_no][current_hit.chan-1];
            current_hit.layer    = layer_info[tdc_no][current_hit.chan-1];
            current_hit.fpc      = fpc_info[tdc_no][current_hit.chan-1];
            
            // code the tdc address in the channel number
            current_hit.chan += channel_number_prefix[tdc_no];
//             cout << "current hit channel: " << current_hit.chan << endl;



            if(current_hit.chan != ref_chan){
              current_hit.t1 += global_t1_shift;
            }

            
            if(current_hit.chan == ref_chan && (got_reference_time == false)){
//               cout << "current hit channel: " << current_hit.chan << endl;
//               cout << "got refchan ! " << endl;
              reference_time = current_hit.t1;
              got_reference_time = true;
            }
            
            my_event.hits.push_back(current_hit);
            
        }
        if (current_hit.trig_no <= trig_no){
          data_tree_index[tdc_no]++;
        } else {
          break;
        }
        
        
      }
      
    }
    
    // make reference time correction, only fill output tree if you have
    // something in your reference channel
    
    if(got_reference_time){
        
      for(Int_t i = 0; i < my_event.hits.size(); i++){
        my_event.hits[i].t1 -= reference_time;

          
      }
        
      joint_tree->Fill();
    }
    
    
    
    if (all_ends_reached) { // all trees have been read to the end
      break;
    }
    
  }
  
  out_file->cd();
  joint_tree->Write();
  

  for (Int_t i = 0; i < TDC_list.size(); i++){
    
    TString tdc(TDC_list[i]);
    
    cout << "found data tree for tdc: " << tdc << endl;
    
    
    TString tdc_number_str( tdc(4,7) );
    Int_t   tdc_number = tdc_number_str.Atoi();
    
    
    
    new TCanvas();
    joint_tree->Draw(Form("hits.chan - %d: hits.t1>>0x%04d_t1_meta(1000,-1000,1000,32,%d,%d)",tdc_number*100,tdc_number,1,1+channels),
            Form("hits.chan > %d && hits.chan < %d",tdc_number*100,tdc_number*100+100),"colz");
    new TCanvas();
    joint_tree->Draw(Form("hits.chan - %d: hits.tot>>0x%04d_tot_meta(1000,0,1000,32,%d,%d)",tdc_number*100,tdc_number,1,1+channels),
            Form("hits.chan > %d && hits.chan < %d",tdc_number*100,tdc_number*100+100),"colz");
    new TCanvas();
    joint_tree->Draw(Form("hits.tot : hits.t1 >>0x%04d_potato(1000,-500,500,1000,0,1000)",tdc_number),
            Form("hits.chan > %d && hits.chan < %d",tdc_number*100,tdc_number*100+100),"colz");
  }




// make coincidence matrix
  
  Event* this_event = new Event();
  joint_tree->SetBranchAddress("event",&this_event);


  TH2F* coinc_matrix = new TH2F("coinc_matrix","coinc_matrix", 500, 35000, 35000+500, 500, 35000, 35000+500);

  TH2F* meta_fish = new TH2F("meta_fish","meta_fish", 500, -250, 250, 500, -250, 250);

  for (Int_t evt_no = 0; evt_no < joint_tree->GetEntries(); evt_no++){

    joint_tree->GetEntry(evt_no); 
    for (Int_t hit_no_a = 0; hit_no_a < this_event->hits.size(); hit_no_a++){
      Int_t hit_a_chan = this_event->hits[hit_no_a].chan;
      for (Int_t hit_no_b = hit_no_a; hit_no_b < this_event->hits.size(); hit_no_b++){
        Int_t hit_b_chan = this_event->hits[hit_no_b].chan;
 
          coinc_matrix->Fill(hit_a_chan,hit_b_chan);
          if ( (hit_a_chan > 35000) && (hit_a_chan < 35100) && (hit_b_chan > 35100) && (hit_b_chan < 35200)){
            if (  
                 // Lena
                 //  (hit_a_chan % 100 -1)  == ( 31 - (hit_b_chan % 100 -1)) ||   /* main diagonal */
                 //  (hit_a_chan % 100 -1)  == ( 32 - (hit_b_chan % 100 -1) )     /* next to diagonal */

                 // Sandra
                  (hit_a_chan % 100 -1)  == (hit_b_chan % 100 -1) 
               ){ 
              Float_t t1_a = this_event->hits[hit_no_a].t1;
              Float_t t1_b = this_event->hits[hit_no_b].t1;
              meta_fish->Fill(t1_a +t1_b, t1_a -t1_b);
            }
          } 
         
      } 
    }

  }

  //coinc_matrix->Write(); // not necessary because histogram
     

  out_file->Write();
  
}
