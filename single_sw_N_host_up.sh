sudo mn -c
sudo -E mn --topo=single,$1 --controller=remote,ip=127.0.0.1,port=6633 --custom=test.py --test=test
