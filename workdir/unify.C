

class Hit {
public:
  int chan;
  int trig_no;
  int ref_chan;
  double t1;
  double tot;
};

class Event {
public:
  std::vector<Hit> hits;
};




void unify(void){
  
  cout << "unify!" <<endl;
  
  
  Int_t ref_chan = 353001; // channel 1 of FPGA 0x0351 is our reference channel!
  
  
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
   
  TTree* data_tree[TDC_list.size()];
  Int_t  channel_number_prefix[TDC_list.size()];
  Int_t data_tree_entries[TDC_list.size()];
  Int_t data_tree_index[TDC_list.size()];
  
  
  
  Hit current_hit;
  
  
  
  ////////////////// make sure you always write into current hit!!! ////////////////
  
  for (Int_t i = 0; i < TDC_list.size(); i++){
    
    TString tdc(TDC_list[i]);
    
    cout << "found data tree for tdc: " << tdc << endl;
    
    
    TString tdc_number_str( tdc(4,7) );
    Int_t   tdc_number = tdc_number_str.Atoi();
//     cout << "TDC number: " <<  tdc_number <<  endl;
    cout << "TDC channel prefix/offset (1000 possible TDC channels left): " <<  tdc_number*1000 <<  endl;
    
    data_tree[i] = (TTree*) f.Get(tdc);
    channel_number_prefix[i] = tdc_number*1000;
    
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
            current_hit.chan += channel_number_prefix[tdc_no];
//             cout << "current hit channel: " << current_hit.chan << endl;
            
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
  out_file->Close();
  delete out_file;
  
  ///// examples for drawing ////
  
  // joint_tree->Draw("hits.t1","hits.chan == 350005")

  
  
}