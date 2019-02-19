FROM opensuse:42.3


##################################################
##              Go4 + dabc + root               ##
##################################################



RUN zypper ref

RUN zypper --non-interactive in \
  wget curl \
  tar zlib \
  cmake gcc gcc-c++ \
  libX11-devel libXext-devel libXft-devel libXpm-devel\
  git subversion \
  libqt4-devel\
  git bash cmake gcc-c++ gcc binutils \
  xorg-x11-libX11-devel xorg-x11-libXpm-devel xorg-x11-devel \
  xorg-x11-proto-devel xorg-x11-libXext-devel \
  gcc-fortran libopenssl-devel \
  pcre-devel Mesa glew-devel pkg-config libmysqlclient-devel \
  fftw3-devel libcfitsio-devel graphviz-devel \
  libdns_sd avahi-compat-mDNSResponder-devel openldap2-devel \
  python-devel libxml2-devel krb5-devel gsl-devel libqt4-devel \
  glu-devel \
  xterm screen xvfb-run x11vnc openbox \
  boost-devel

RUN svn co https://subversion.gsi.de/dabc/trb3  

RUN cd trb3; make -j4; cat $(find . -iname "makelog.txt")
### root, go4, dabc and stream are successfully installed!




##################################################
##              trbnet + daqtools               ##
##################################################


RUN zypper --non-interactive in \
  vim \
  dhcp-server\
  rpcbind \
  gnuplot \
  ImageMagick \
  perl-XML-LibXML \
  glibc-locale \
  tmux \
  xorg-x11-Xvnc \
  emacs \
  htop \
  ncdu \
  psmisc \
  python-jsonpath-rw \
  python-pip

RUN pip install --upgrade pip; pip install pandas
  
RUN cpan Data::TreeDumper Date::Format File::chdir

RUN zypper --non-interactive in \
  libtirpc-devel

RUN git clone git://jspc29.x-matter.uni-frankfurt.de/projects/trbnettools.git;\
  cd /trbnettools; \
  git checkout 02cf


RUN cd /trbnettools/libtrbnet_perl; \
 perl Makefile.PL; \
 cd /trbnettools; \
 make clean; 

RUN cd /trbnettools; \
 make TRB3=1

RUN cd /trbnettools; \
 make TRB3=1 install

RUN echo "/trbnettools/liblocal" >> /etc/ld.so.conf.d/trbnet.conf;\
 ldconfig -v

ENV PATH=$PATH:/trbnettools/bin

RUN git clone git://jspc29.x-matter.uni-frankfurt.de/projects/daqtools.git

RUN cd daqtools/xml-db; \
 ./xml-db.pl

##################################################
##                patches + misc                ##
##################################################

### replace httpi with a modified version, because the httpi in daqtools won't run as root
COPY build_files/httpi /daqtools/web/httpi

RUN . /trb3/trb3login

RUN cd /trb3/; . /trb3/trb3login;  make -j4 update

## 2019-02-11  - - fix strange dabc error
RUN cd /trb3/; . /trb3/trb3login;  make -j4 update

RUN zypper --non-interactive in \
   firefox \
   lxpanel

RUN pip install prettytable python2-pythondialog
