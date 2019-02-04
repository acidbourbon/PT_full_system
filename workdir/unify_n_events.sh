#!/bin/bash

n=$1

rm *.root; tree_out=true go4analysis -number $n -stream localhost:6790; root -l unify.C
