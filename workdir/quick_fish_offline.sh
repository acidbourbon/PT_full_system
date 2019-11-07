#!/bin/bash

number=1000
data_dir=$1
if [ -e $data_dir/joint_tree_prev$number.root ]; then
echo "was already unpacked"
#root -l $data_dir/*.root
else
./go4_offline.sh $data_dir/*.hld -number $number
./correlation.sh 
cp joint_tree.root  $data_dir/joint_tree_prev$number.root
cp correlation.root $data_dir/correlation_prev$number.root
echo "unpacking"
fi
