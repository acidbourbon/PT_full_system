##################################################
##        get minimal distro from cloud         ##
##################################################


FROM go4_trbnet_leap_15.0_stable_2019-03-01


RUN zypper ref && zypper --non-interactive install python-numpy python-pandas python-scipy python-matplotlib
