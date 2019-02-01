#!/bin/bash

echo "container started"

echo "create main tmux session"

echo "run /conf/conf.sh"
. /conf/conf.sh

cd /workdir
tmux new -d -s main



tmux link-window -s cts_gui:cts_gui -t main
tmux link-window -s vnc:vnc -t main


tmux new-window -t main -n "dabc" "dabc_exe TdcEventBuilder_noHLD.xml;/bin/bash"


tmux new-window -t main -n "go4" "rm Go4AutoSave.root;  go4 my_hotstart.hotstart;/bin/bash"

# tmux new-window -t main -n "htop" "htop;/bin/bash"
tmux new-window -t main -n "info" "cat /conf/conf_log.txt; cat info.txt; /bin/bash"
tmux new-window -t main -n "PT_ctrl" "cd /workdir/pasttrec_ctrl; /bin/bash"
tmux new-window -t main -n "new" "/bin/bash"
tmux new-window -t main -n "new" "/bin/bash"
tmux new-window -t main -n "new" "/bin/bash"
tmux new-window -t main -n "new" "/bin/bash"
tmux new-window -t main -n "new" "/bin/bash"
tmux select-window -t main:info


tmux a -t main




echo "drop user to shell"
/bin/bash

echo "terminate container"