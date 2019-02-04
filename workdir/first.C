// this is example for


#include <stdlib.h>

void first()
{
  //base::ProcMgr::instance()->SetRawAnalysis(true);
    base::ProcMgr::instance()->SetTriggeredAnalysis(true);

   // all new instances get this value
   base::ProcMgr::instance()->SetHistFilling(4);

   // this limits used for liner calibrations when nothing else is available
   hadaq::TdcMessage::SetFineLimits(10, 510);

   // default channel numbers and edges mask
   hadaq::TrbProcessor::SetDefaults(33, 0x2);
//    hadaq::TdcProcessor::SetDefaults(1000);
   //hadaq::TdcProcessor::DisableCalibrationFor(0,8);
   // [min..max] range for TDC ids
   //hadaq::TrbProcessor::SetTDCRange(0x610, 0x613);
   hadaq::TrbProcessor::SetTDCRange(0x0350, 0x0353);

   // configure ToT calibration parameters
   // first - minimal number of counts in ToT histogram
   // second - maximal RMS value 
   hadaq::TdcProcessor::SetToTCalibr(100, 0.2); 

   //hadaq::T
   // [min..max] range for HUB ids
   hadaq::TrbProcessor::SetHUBRange(0xc001, 0xcfff);

   // when first argument true - TRB/TDC will be created on-the-fly
   // second parameter is function name, called after elements are created
   hadaq::HldProcessor* hld = new hadaq::HldProcessor(true, "after_create");

   const char* calname = getenv("CALNAME");
   if ((calname==0) || (*calname==0)) calname = "test_";
   const char* calmode = getenv("CALMODE");
   int cnt = (calmode && *calmode) ? atoi(calmode) : 0;
   const char* caltrig = getenv("CALTRIG");
   unsigned trig = (caltrig && *caltrig) ? atoi(caltrig) : 0x0;
   const char* uset = getenv("USETEMP");
   unsigned use_temp = 0; // 0x80000000;
   if ((uset!=0) && (*uset!=0) && (strcmp(uset,"1")==0)) use_temp = 0x80000000;

   printf("HLD configure calibration calfile:%s  cnt:%d trig:%X temp:%X\n", calname, cnt, trig, use_temp);

   // first parameter if filename  prefix for calibration files
   //     and calibration mode (empty string - no file I/O)
   // second parameter is hits count for autocalibration
   //     0 - only load calibration
   //    -1 - accumulate data and store calibrations only at the end
   //    >0 - automatic calibration after N hits in each active channel
   // third parameter is trigger type mask used for calibration
   //   (1 << 0xD) - special 0XD trigger with internal pulser, used also for TOT calibration
   //    0x3FFF - all kinds of trigger types will be used for calibration (excluding 0xE and 0xF)
   //   0x80000000 in mask enables usage of temperature correction
//   hld->ConfigureCalibration(calname, cnt, /*(1 << trig) | use_temp*/ 0x3fff);
   hld->ConfigureCalibration("test_", -1, (1 << 0xD)); 
 

   // only accept trigger type 0x1 when storing file
   //new hadaq::HldFilter(0x0);

   // create ROOT file store
//    base::ProcMgr::instance()->CreateStore("td.root");

   // 0 - disable store
   // 1 - std::vector<hadaq::TdcMessageExt> - includes original TDC message
   // 2 - std::vector<hadaq::MessageFloat>  - compact form, without channel 0, stamp as float (relative to ch0)
   // 3 - std::vector<hadaq::MessageDouble> - compact form, with channel 0, absolute time stamp as double
   base::ProcMgr::instance()->SetStoreKind(1);

}

// extern "C" required by DABC to find function from compiled code

extern "C" void after_create(hadaq::HldProcessor* hld)
{
   printf("Called after all sub-components are created\n");

   if (hld==0) return;

   for (unsigned k=0;k<hld->NumberOfTRB();k++) {
      hadaq::TrbProcessor* trb = hld->GetTRB(k);
      if (trb==0) continue;
      printf("Configure %s!\n", trb->GetName());
      trb->SetPrintErrors(10);
   }

   unsigned firsttdc = 0;

   for (unsigned k=0;k<hld->NumberOfTDC();k++) {
      hadaq::TdcProcessor* tdc = hld->GetTDC(k);
      if (tdc==0) continue;

      if (firsttdc == 0) firsttdc = tdc->GetID();

      printf("Configure %s!\n", tdc->GetName());

      // try to build abs time difference between 0 channels
      //      if (tdc->GetID() != firsttdc)
      //   tdc->SetRefChannel(0, 0, (0x70000 | firsttdc), 6000,  -20., 20.);

      tdc->SetUseLastHit(false);
      
      // tdc->DisableCalibrationFor(0);

      // if (tdc->GetID() == 0x1130);
      
      for (int n=1;n<49;++n)
         tdc->SetRefChannel(n,0, 0xffff, 6000, -200, 200); // LED DIFF
   }
}


