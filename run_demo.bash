#clean remains of old mininet sessions
./reset_mininet.bash
#copy some data into the mininet folder
cp RingNetwork.json ../../mininet/RingNetwork.json
cp build_network.py ../../mininet
sudo python ../../mininet/build_network.py --behavioral-exe $PWD/bm --json $PWD/bfr.json --pcap-dump test.json
