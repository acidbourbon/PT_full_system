#ifndef MdcProcessor_h
#define MdcProcessor_h

#include "hadaq/SubProcessor.h"

namespace hadaq {

  class TrbProcessor;

  /** This is specialized sub-processor for custom data.
   * It should be used together with TrbProcessor,
   * which the only can provide data
   **/

  class MdcProcessor : public SubProcessor {

    friend class TrbProcessor;

  protected:

    base::H2handle HitsPerBinRising;
    base::H2handle HitsPerBinFalling;
    base::H2handle ToT;
    base::H2handle deltaT;
    base::H1handle Errors;
    base::H2handle  meta_potato_h;
      base::H1handle  meta_t1_h;
      base::H1handle  meta_tot_h;
      base::H2handle  meta_tot_2d;
      base::H2handle  meta_t1_2d;


  public:

    MdcProcessor(TrbProcessor* trb, unsigned subid);
    virtual ~MdcProcessor() {}


    /** Scan all messages, find reference signals
     * if returned false, buffer has error and must be discarded */
    virtual bool FirstBufferScan(const base::Buffer&);

    /** Scan buffer for selecting messages inside trigger window */
    virtual bool SecondBufferScan(const base::Buffer&) { return true; }
  };

}



hadaq::MdcProcessor::MdcProcessor(TrbProcessor* trb, unsigned subid) :
hadaq::SubProcessor(trb, "MDC_%04X", subid)
{
  HitsPerBinRising      = MakeH2("HitsPerBinRising", "", 33,-1,32,8,0,8);
  HitsPerBinFalling      = MakeH2("HitsPerBinFalling", "", 33,-1,32,8,0,8);
  ToT      = MakeH2("ToT", "", 32,0,32,400,0,800, "channel#; ToT [ns]");
  deltaT   = MakeH2("deltaT", "", 32,0,32,2000,-1000,1000 , "channel#; t1 [ns]");
  Errors   = MakeH1("Errors", "", 33,-1,32);
  float_t t1_L = -1500;
  float_t t1_R = -500;
  float_t tot_L = 0;
  float_t tot_R = 600;
  meta_t1_h = MakeH1("meta_t1","meta_t1", 2000, t1_L, t1_R, "t1 [ns]");
  meta_t1_2d = MakeH2("meta_t1_2d","meta_t1_2d", 2000, t1_L, t1_R,32,0.5,32.5, "t1 [ns];channel#");
  meta_tot_h = MakeH1("meta_tot","meta_tot", 4000, tot_L, tot_R, "ns");
  meta_tot_2d = MakeH2("meta_tot_2d","meta_tot_2d", 2000, tot_L, tot_R,32,0.5,32.5, "ToT [ns];channel#");
  meta_potato_h = MakeH2("meta_potato","meta_potato",2500,t1_L,t1_R,1501, tot_L, tot_R, "t1 [ns];tot [ns]");
   ((TObject*) meta_t1_2d)->SetDrawOption("colz");
   ((TH2F*) meta_tot_2d)->SetDrawOption("COLZ");
   ((TObject*) meta_potato_h)->SetDrawOption("colz");       
}

bool hadaq::MdcProcessor::FirstBufferScan(const base::Buffer &buf)
{
  uint32_t* arr = (uint32_t*) buf.ptr();
  unsigned len = buf.datalen()/4;

  uint32_t data = arr[0];
  FillH2(HitsPerBinRising,-1,data&0x7);
  signed reference = data&0x1FFF;

  for (unsigned n=1;n<len;n++) {
    uint32_t data = arr[n];
    unsigned channel = data>>27;

    if((data>>26)&1) {
      FillH1(Errors,channel);
    }
    else {
      signed risingHit  = (data>>13) & 0x1fff;
      signed fallingHit = (data>>0) & 0x1fff;
      float timeDiff = (risingHit - reference)*0.4;
      if ( reference < risingHit) 
            timeDiff = (risingHit - reference + 0x2000)*0.4;
      float timeOverThreshold = (fallingHit - risingHit)*0.4;
      if (fallingHit < risingHit) 
            timeOverThreshold = (fallingHit - risingHit + 0x2000)*0.4;

      FillH2(HitsPerBinRising, channel, risingHit & 0x7);
      FillH2(HitsPerBinFalling, channel, fallingHit & 0x7);
      FillH2(deltaT, channel, timeDiff);
      FillH2(ToT,    channel, timeOverThreshold);

      FillH2(meta_potato_h, timeDiff, timeOverThreshold);
      //FillH2(meta_times_h, timeDiff, timeOverThreshold);      
      FillH1(meta_tot_h, timeOverThreshold);
      FillH1(meta_t1_h, timeDiff );
      FillH2(meta_tot_2d, timeOverThreshold, channel);
      FillH2(meta_t1_2d, timeDiff, channel);
      
    }
  }
  return true;
}

#endif
