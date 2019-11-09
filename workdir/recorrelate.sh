#!/bin/bash

data_dir=$1
for i in $data_dir/joint_tree*root ; do
ln -s $i joint_tree.root
./correlation.sh 
cp correlation.root $(echo $i | sed "s/joint_tree/correlation/")
rm joint_tree.root
done
