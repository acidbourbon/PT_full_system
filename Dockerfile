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


RUN cpan File::chdir XML::LibXML Data::TreeDumper CGI::Carp

# newest commit
#ENV DAQTOOLS_COMMIT=master

# newest commit from 2018-02-28
ENV DAQTOOLS_COMMIT=4840d304ad9cce93ffe972ef8cff4c325d7ac198 

#################################################

RUN git clone git://jspc29.x-matter.uni-frankfurt.de/projects/daqtools.git && \
  cd /daqtools && \
  git checkout $DAQTOOLS_COMMIT && \
  cd /daqtools/xml-db && \
 ./xml-db.pl




ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && \
  apt-get -y install \
  tmux \
  lxpanel \
  firefox \
  gzip \
  dialog \
  isc-dhcp-server \
  htop \
  ncdu \
  openbox

RUN apt-get update && \
  apt-get -y install \
  vim \
  tigervnc-standalone-server

RUN apt-get update && \
  apt-get -y install \
  rpcbind \
  gnuplot
  

### replace httpi with a modified version, because the httpi in daqtools won't run as root
COPY build_files/httpi /daqtools/web/httpi



##################################################
##                    midori                    ##
##################################################

RUN apt-get update && \
  apt-get -y install \
  cmake valac libwebkit2gtk-4.0-dev libgcr-3-dev libpeas-dev libsqlite3-dev libjson-glib-dev libarchive-dev intltool libxml2-utils

RUN git clone https://github.com/midori-browser/core.git; mv /core /midori

RUN cd /midori && \
mkdir _build && \
cd _build && \
cmake -DCMAKE_INSTALL_PREFIX=/usr .. && \
make && \
make install



##################################################
##               chromium browser               ##
##################################################

RUN apt-get update && \
  apt-get -y install \
  chromium-browser

  

ENV HOME=/workdir

RUN pip3 install jupyter

RUN cd /opt; git clone https://github.com/lambdalisue/jupyter-vim-binding

RUN apt-get update && \
  apt-get -y install \
  picocom

RUN pip3 install pyserial
RUN pip3 install pandas
RUN pip3 install trbnet

RUN apt-get update && \
  apt-get -y install \
  nano \
  parallel \
  imagemagick

RUN apt-get update && \
  apt-get -y install \
  texlive-xetex \
  pandoc 

RUN apt-get -y install emacs

RUN apt-get -y install img2pdf
# RUN pip install scipy==1.1.0
    

#RUN echo "#!/bin/bash\n. /root-build/bin/thisroot.sh" >entrypoint.sh ; chmod +x entrypoint.sh
#
#RUN echo "cd /workdir/; /bin/bash" >> entrypoint.sh
#
#
#ENTRYPOINT "/entrypoint.sh"
