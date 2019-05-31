##################################################
##        get minimal distro from cloud         ##
##################################################


FROM go4_trbnet_leap_15.0_stable_2019-03-01


RUN zypper ref && zypper --non-interactive install python-numpy python-pandas python-scipy python-matplotlib
RUN zypper ref && zypper --non-interactive install iproute2 iputils 
RUN zypper ref && zypper --non-interactive install -t pattern network_admin
RUN zypper ref && zypper --non-interactive install python3-pip
RUN zypper ref && zypper --non-interactive install python3-curses

RUN pip3 install setuptools visidata pypng

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN zypper ref && zypper --non-interactive install nano
