#!/bin/bash
#for i in $(ls -d  data/*/); do ./quick_fish_offline.sh $i; done
for i in $(find data -iname "20*"); do echo process $i; ./recorrelate.sh $i; done
