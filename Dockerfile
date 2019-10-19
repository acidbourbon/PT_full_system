
# the following uncommented lines are the Dockerfile contents of
# image acidbourbon/ubuntu_cernroot_python3
# we're gonna save ourselves the effort of compiling root by using a prebuilt container

# #---------------------------
# 
# ##################################################
# ##    intermediate stage to build CERN ROOT     ##
# ##################################################
# 
# 
# FROM ubuntu:18.04
# 
# USER root
# 
# ARG DEBIAN_FRONTEND=noninteractive
# 
# RUN apt-get update && \
#   apt-get -y install \
#   libgslcblas0 \
#   python3-numpy \
#   python3-scipy \
#   python3-matplotlib \
#   liblapack3 \
#   libboost-all-dev \
#   wget \
#   git dpkg-dev cmake g++ gcc binutils libx11-dev libxpm-dev \
#   libxft-dev libxext-dev
# 
# RUN wget https://root.cern/download/root_v6.18.02.source.tar.gz && tar -zxvf root_v6.18.02.source.tar.gz && rm root_v6.18.02.source.tar.gz
# 
# # arguments for cmake to use python3 for pyROOT
# RUN mkdir /root-build && cd /root-build; cmake -DPYTHON_EXECUTABLE=/usr/bin/python3 ../root-6.18.02
# 
# RUN cd /root-build; make -j6
# 
# ##################################################
# ##        build actual working container        ##
# ##################################################
# 
# # leave some 500 MB of root source files behind
# 
# FROM ubuntu:18.04
# 
# USER root
# 
# ARG DEBIAN_FRONTEND=noninteractive
# 
# RUN apt-get update && \
#   apt-get -y install \
#   vim \
#   nano \
#   libgslcblas0 \
#   python3-numpy \
#   python3-scipy \
#   python3-matplotlib \
#   bc \
#   liblapack3 \
#   libboost-all-dev 
# 
# 
# COPY --from=0 /root-build /root-build 
# 
# 

# FROM acidbourbon/ubuntu_cernroot_python3:2019-09-29
FROM ubuntu:18.04

USER root

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
  apt-get -y install \
  gv ghostscript xterm x11-utils \
  dialog \
  libgfortran3 \
  libgslcblas0 \
  wine-stable \
  iputils-ping \
  curl \
  perl \
  git \
  python3-pip \
  liblapack3 \
  libboost-all-dev \
  libgslcblas0 \
  python3-numpy \
  python3-scipy \
  python3-matplotlib \
  wget \
  psmisc \
  git dpkg-dev cmake g++ gcc binutils libx11-dev libxpm-dev \
  libxft-dev libxext-dev \
  gfortran libssl-dev libpcre3-dev \
  xlibmesa-glu-dev libglew1.5-dev libftgl-dev \
  libmysqlclient-dev libfftw3-dev libcfitsio-dev \
  graphviz-dev libavahi-compat-libdnssd-dev \
  libldap2-dev python-dev libxml2-dev libkrb5-dev \
  libgsl0-dev libqt4-dev \
  subversion
  
  
RUN pip3 install --upgrade pip
RUN pip3 install setuptools && \
  pip3 install pythondialog python-vxi11

# for garfield to feel at home make symlink to som gsl libs
RUN ln -s /usr/lib/x86_64-linux-gnu/libgslcblas.so.0.0.0 /usr/lib/libgsl.so.0 

# this will create /LTspiceXVII with all the 
# windows binaries and libraries you'll need
#ADD ./build/LTspiceXVII.tgz /

ENV HOME=/workdir

RUN echo "#!/bin/bash\n. /root-build/bin/thisroot.sh" >entrypoint.sh ; chmod +x entrypoint.sh

RUN echo "cd /workdir/; /bin/bash" >> entrypoint.sh


ENTRYPOINT "/entrypoint.sh"


##################################################
##              Go4 + dabc + root               ##
##################################################

# newest commit
#ENV DABC_TRB3_REV=HEAD

# newest commit from 2018-02-28
ENV DABC_TRB3_REV=4242 

##################################################

RUN svn checkout -r $DABC_TRB3_REV https://subversion.gsi.de/dabc/trb3  

# Patch Makefile to enable python3 in root compilation

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



RUN pip3 install setuptools visidata pypng

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
