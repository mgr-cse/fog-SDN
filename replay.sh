sudo mn -c
sudo -E mn --topo=mytopo --controller=remote,ip=127.0.0.1,port=6633 --custom=replay.py --test=test
