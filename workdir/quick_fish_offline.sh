#!/bin/bash

data_dir=$
./go4_offline.sh $data_dir
./correlations.sh 
cp joint_tree.root correlations.root $data_dir/
