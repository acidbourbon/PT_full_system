##################################################
##        get minimal distro from cloud         ##
##################################################

FROM opensuse/leap:15.0



##################################################
##                prerequisites                 ##
##################################################

### install system packages with opensuse package manager
RUN zypper ref && zypper --non-interactive in \
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
  boost-devel \
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
  python-pip \
  firefox \
  lxpanel \
  libtirpc-devel \
  perl-File-chdir \
  perl-TimeDate \
  gzip \
  tig \
  python-numpy \
  dialog


### install perl modules from cpan ###
RUN cpan Data::TreeDumper CGI::Carp

### install python modules from pip ###
RUN pip install --upgrade pip && pip install prettytable python2-pythondialog

# ##################################################
# ##                root + python3                ##
# ##################################################
# 
# RUN wget https://root.cern/download/root_v6.18.02.source.tar.gz && tar -zxvf root_v6.18.02.source.tar.gz && rm root_v6.18.02.source.tar.gz
# 
# RUN zypper ref && zypper --non-interactive in \
#   python3-numpy python3-matplotlib python3-pip
# 
# # arguments for cmake to use python3 for pyROOT
# RUN mkdir /root-build && cd /root-build; \
#   cmake \
#   -DPYTHON_EXECUTABLE=/usr/bin/python3 \
#   -DPYTHON_LIBRARY=/usr/lib64/python3.6 \
#   -DPYTHON_INCLUDE_DIR=/usr/include/python3.6m \
#   ../root-6.18.02
#   
# #  -DPYTHON_LIBRARIES=/usr/lib/x86_64-linux-gnu/libpython3.6m.so \
# #  -DPYTHON_INCLUDE_DIR=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())")  \
# #   -Dpython_version=3.6 \
#   
# 
# RUN cd /root-build; make -j6
# 



##################################################
##              Go4 + dabc + root               ##
##################################################

# newest commit
#ENV DABC_TRB3_REV=HEAD

# newest commit from 2018-02-28
ENV DABC_TRB3_REV=4242 

##################################################

RUN svn checkout -r $DABC_TRB3_REV https://subversion.gsi.de/dabc/trb3  

### patch the makefile, so root is compiled against python3 not python2
RUN perl -pi -e "s/-Dhttp=ON/-Dhttp=ON -DPYTHON_EXECUTABLE=\/usr\/bin\/python3/;" /trb3/Makefile

RUN cd /trb3; \
  > /tmp/trb3_make_exit_value; \
  { make -j2; echo $? > /tmp/trb3_make_exit_value; killall tail; }& \
  echo -e "\n\n---- display make log: ----\n\n"; \
  tail -F ./stream/makelog.txt & \
  tail -F ./go4/makelog.txt & \
  tail -F ./dabc/makelog.txt & \
  tail -F ./rootbuild/makelog.txt & \
  wait; \
  echo -e "\n\n---- end of make log: ----\n\n"; \
  $( exit $(cat /tmp/trb3_make_exit_value) )



##################################################
##                    trbnet                    ##
##################################################

# newest commit
#ENV TRBNET_COMMIT=master

# last stable commit
ENV TRBNET_COMMIT=02cf41a486d64bc894986fe87c174bfe1b07fc9b 
# newest version of trbnettools does not work with this system ... revert to older commit ###
# has something to do with commit 0cd022a9b0bda2213989eef118a1dda077794ba9 
# 2019-01-24 00:17 Michael Traxler ----  added -ltirpc in Makesfiles for a working RPC implementation, mt 
# commit breaks rpc communication

##################################################

RUN git clone git://jspc29.x-matter.uni-frankfurt.de/projects/trbnettools.git &&\
  cd /trbnettools &&\
  git checkout $TRBNET_COMMIT &&\
  cd /trbnettools/libtrbnet_perl && \
  perl Makefile.PL && \
  cd /trbnettools && \
  make clean && \
  make TRB3=1 && \
  make TRB3=1 install && \
  echo "/trbnettools/liblocal" >> /etc/ld.so.conf.d/trbnet.conf && \
  ldconfig -v

ENV PATH=$PATH:/trbnettools/bin




##################################################
##                   daqtools                   ##
##################################################

# newest commit
#ENV DAQTOOLS_COMMIT=master

# newest commit from 2018-02-28
ENV DAQTOOLS_COMMIT=4840d304ad9cce93ffe972ef8cff4c325d7ac198 

##################################################

RUN git clone git://jspc29.x-matter.uni-frankfurt.de/projects/daqtools.git && \
  cd /daqtools && \
  git checkout $DAQTOOLS_COMMIT && \
  cd /daqtools/xml-db && \
 ./xml-db.pl

### replace httpi with a modified version, because the httpi in daqtools won't run as root
COPY build_files/httpi /daqtools/web/httpi





RUN zypper ref && zypper --non-interactive install python-numpy python-pandas python-scipy python-matplotlib
RUN zypper ref && zypper --non-interactive install python3-numpy python3-pandas python3-scipy python3-matplotlib
RUN zypper ref && zypper --non-interactive install iproute2 iputils 
RUN zypper ref && zypper --non-interactive install -t pattern network_admin
RUN zypper ref && zypper --non-interactive install python3-pip
RUN zypper ref && zypper --non-interactive install python3-curses

RUN pip3 install setuptools visidata pypng

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN zypper ref && zypper --non-interactive install nano








##################################################
##          additional changes/updates          ##
##################################################

# go ahead, customize your container 
# delete/comment out changes to revert them again and return
# to a previous state

### install additional perl modules from cpan ###
#RUN cpan ExamplePerlModule

### install python modules from pip ###
#RUN pip install --upgrade pip && pip install example_python_module

### install additional system packages with opensuse package manager
#RUN zypper refresh && zypper --non-interactive in \
#  example_package_1 \
#  example_package_2 \
#  example_package_3


##################################################
## update dabc/stream/go4 to the newest version ##
##################################################

#RUN cd /trb3/; . /trb3/trb3login;  make -j4 update



##################################################
##               update daqtools                ##
##################################################

#RUN cd /daqtools; git checkout master; git pull &&\
#  cd /daqtools/xml-db && \
# ./xml-db.pl

### overwrite httpi again with a custom version so it can run as root
#COPY build_files/httpi /daqtools/web/httpi 


##################################################
##              update trbnettools              ##
##################################################

#RUN  cd /trbnettools &&\
#  git checkout master &&\
#  git pull &&\
#  cd /trbnettools/libtrbnet_perl && \
#  perl Makefile.PL && \
#  cd /trbnettools && \
#  make clean && \
#  make TRB3=1 && \
#  make TRB3=1 install && \
#  ldconfig -v
