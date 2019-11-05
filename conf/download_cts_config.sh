#!/bin/bash

wget http://localhost:1148/cts/cts.pl?dump,shell
mv cts.pl\?dump\,shell conf_cts.sh
chmod +x conf_cts.sh

