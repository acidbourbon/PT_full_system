#!/bin/bash

rm *.root; tree_out=true go4analysis -user $@
root -b -l unify.C -q
