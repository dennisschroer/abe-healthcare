#!/usr/bin/env bash
sudo apt -qq update
sudo apt install git
sudo apt install -y python3 python3-dev python3-setuptools
sudo apt install -y libgmp10 libgmp-dev libgmp3c2
wget https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz
tar -xvzf pbc-0.5.14.tar.gz
cd pbc-0.5.14
# HIER GEBLEVEN
./configure
make
make install
sudo dpkg -i libpbc0_0.5.12_amd64.deb
sudo dpkg -i libpbc-dev_0.5.12_amd64.deb
sudo apt-get install -y openssl libssl-dev
git clone git@github.com:denniss17/charm.git