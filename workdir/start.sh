#!/bin/bash

# set home to workdir
if [ $(whoami) != "root" ]; then export HOME=/workdir ;fi

echo "container started"

echo "create main tmux session"

echo "run /conf/conf.sh"
. /conf/conf.sh # keep environment variables set in conf.sh

cd /workdir

# remove vim swap files 
rm $(find . -iname "*swo*")
rm $(find . -iname "*swp*")
rm $(find . -iname "*swa*")
rm $(find /conf -iname "*swo*")
rm $(find /conf -iname "*swp*")
rm $(find /conf -iname "*swa*")

cp web_hack/tdc.htm /daqtools/web/htdocs/tdc/tdc.htm
cp web_hack/jquery-3.4.1.min.js /daqtools/web/htdocs/tdc/jquery-3.4.1.min.js


# create new tmux session named "main"
tmux new -d -s main

# display some info
tmux new-window -t main -n "info" "cat /conf/conf_log.txt; cat info.txt; /bin/bash"

tmux link-window -s cts_gui:cts_gui -t main  # attach window opened by conf.sh
tmux link-window -s vnc:vnc -t main          # attach window opened by conf.sh




tmux new-window -t main -n "dabc" "dabc_exe TdcEventBuilder_noHLD.xml;/bin/bash"


#tmux new-window -t main -n "go4" "rm *.root;  go4 0350_meta.hotstart;/bin/bash"


GO4_WEB_PORT=8080
tmux new-window -t main -n "go4_ana" "rm *.root; tree_out=false go4analysis -stream localhost:6790 -http localhost:$GO4_WEB_PORT;/bin/bash"

#tmux new-window -t main -n "PT_ctrl" "cd /workdir/pasttrec_ctrl; /bin/bash"
tmux new-window -t main -n "new" "/bin/bash"
tmux new-window -t main -n "new" "/bin/bash"
tmux new-window -t main -n "new" "/bin/bash"
tmux new-window -t main -n "new" "/bin/bash"
tmux new-window -t main -n "new" "/bin/bash"
# open CTS GUI and GO4 Web interface in firefox (running in VNC)
#tmux new-window -t main -n "x11_apps" "sleep 5 && firefox -new-tab -url localhost:$CTS_GUI_PORT -new-tab -url localhost:$GO4_WEB_PORT& /bin/bash"
tmux new-window -t main -n "sc_web"  "sleep 5  && midori http://localhost:$CTS_GUI_PORT & /bin/bash"
tmux new-window -t main -n "cts_web" "sleep 5 && midori -a http://localhost:$CTS_GUI_PORT/cts/cts.htm & /bin/bash"
tmux new-window -t main -n "tdc_web" "sleep 5 && midori -a http://localhost:$CTS_GUI_PORT/tdc/tdc.htm & /bin/bash"
tmux new-window -t main -n "ana_web" "sleep 5 && midori -a http://localhost:$GO4_WEB_PORT& /bin/bash"
tmux select-window -t main:info


tmux a -t main




echo "drop user to shell"
/bin/bash

echo "terminate container"
