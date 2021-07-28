killall go4analysis
export CALMODE=0;
rm Go4AutoSave.root; cd /trb3/stream ; make -j4 ; cd /workdir ; tree_out=false go4analysis -stream localhost:6789 -http localhost:8080;
#rm Go4AutoSave.root; tree_out=false go4analysis -stream hadesp63:6789 -http localhost:8080;
#rm Go4AutoSave.root; tree_out=false go4analysis -stream 192.168.103.126:6789 -http localhost:8080;
