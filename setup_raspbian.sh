# ssh-copy-id -i ~/.ssh/id_rsa.pub pi@192.168.100.12
passwd
sudo apt-get update
sudo apt-get upgrade -y
curl -sSL https://get.docker.com | sh
sudo curl -L https://github.com/docker/compose/releases/download/1.16.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
sudo usermod -aG docker pi
sudo apt-get install vim python3-rpi.gpio ipython3 python-pip  -y
pip install pip -U
sudo pip install docker-compose

