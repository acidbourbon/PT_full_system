#!/bin/bash

data_dir=$1
for i in $data_dir/joint_tree*root ; do
outfile=$(echo $i | sed "s/joint_tree/correlation/")
outfile_moddate=0

if [ -e $outfile ]; then
outfile_moddate=$(stat -c %Y $outfile)
fi

correlation_C_moddate=$(stat -c %Y correlation.C)
correlation_h_moddate=$(stat -c %Y correlation.h)
echo "outfile" $outfile
if [ $outfile_moddate -lt $correlation_C_moddate  -o  $outfile_moddate -lt $correlation_h_moddate ]; then
  if [ -e joint_tree.root ]; then
    rm joint_tree.root
  fi
  ln -s $i joint_tree.root
  ./correlation.sh 
  cp correlation.root $outfile
  rm joint_tree.root
else
  echo "already up to date"
fi
done
