#!/bin/bash

id=$1
for i in data/*$id*; do ./recorrelate.sh $i; done
