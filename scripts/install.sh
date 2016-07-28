sudo apt update
sudo apt install git
sudo apt install -y python3 python3-pip python3-dev python3-setuptools
sudo apt install -y libgmp10 libgmp-dev libgmp3c2
if [ "$(sudo ldconfig -p | grep libpbc)" ]
then
wget https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz
tar -xvzf pbc-0.5.14.tar.gz
(cd pbc-0.5.14 && ./configure)
make -C ./pbc-0.5.14
sudo make install -C ./pbc-0.5.14
fi
sudo apt-get install -y openssl libssl-dev
git clone https://github.com/denniss17/charm.git
(cd ./charm && git checkout dev && git pull)
pip3 install -r charm/requirements.txt
(cd ./charm && ./configure.sh)
make -C ./charm
sudo make install -C ./charm
git clone git@github.com:denniss17/abe-healthcare.git
(cd ./abe-healthcare && git checkout master && git pull)
pip3 install -r abe-healtchare/requirements.txt
pip3 install -r abe-healtchare/test-requirements.txt