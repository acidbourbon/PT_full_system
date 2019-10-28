#!/bin/bash

events=$1
rm *.root; tree_out=true go4analysis -number $events -stream localhost:6790; root -b -l unify.C -q; ./rbrowse joint_tree.root
