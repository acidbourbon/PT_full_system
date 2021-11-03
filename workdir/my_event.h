#ifndef Hit_h
#define Hit_h
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
#endif 

#ifndef Event_h
#define Event_h
class Event {
public:
  std::vector<Hit> hits;
};
#endif 
