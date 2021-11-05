#!/bin/bash

sec=$1 
rm *.root
tree_out=true go4analysis -number 0 -stream localhost:6789 &
go4pid=$!
sleep $sec # wait $sec seconds
kill -s SIGINT $go4pid # send termination signal to go4analysis
wait # wait for go4analysis to finish
#./rbrowse tree_out.root
# optional: display data in tbrowser
# combine sindle TDC trees to  on  single data tree 
root -b -l unify.C -q
#./rbrowse joint_tree.root
