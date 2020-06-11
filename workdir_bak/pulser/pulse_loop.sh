# perl -e 'while(1) { print qx(./pulse_sent.sh); <stdin> } '     
./pulse_setup.sh

while true
do
 ./pulse_sent.sh
sleep 2s
done

