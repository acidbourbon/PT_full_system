
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

