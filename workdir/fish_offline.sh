#!/bin/bash

data_dir=$1
if [ -e $data_dir/joint_tree.root ]; then
echo "was already unpacked"
#root -l $data_dir/*.root
else
./go4_offline.sh $data_dir/*.hld 
./correlation.sh 
cp joint_tree.root  $data_dir/joint_tree.root
cp correlation.root $data_dir/correlation.root
echo "unpacking"
fi
