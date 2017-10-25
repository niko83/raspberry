# ssh-copy-id -i ~/.ssh/id_rsa.pub pi@192.168.100.12
passwd
sudo apt-get update
sudo apt-get upgrade -y
curl -sSL https://get.docker.com | sh
sudo curl -L https://github.com/docker/compose/releases/download/1.16.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
sudo usermod -aG docker pi
sudo apt-get install vim python3-rpi.gpio ipython3 python-pip  -y
pip install pip -U
# sudo pip install docker-compose


sudo apt-get install graphite-carbon
# /etc/default/graphite-carbon
# CARBON_CACHE_ENABLED=true
sudo apt-get install python python-pip build-essential python-dev libcairo2-dev libffi-dev
sudo pip install graphite-api


#sudo apt-get install apache2 libapache2-mod-wsgi

sudo unlink /etc/apache2/sites-enabled/000-default.conf
sudo ln -s /home/pi/raspberry/graphite.conf /etc/apache2/sites-enabled/graphite.conf
sudo ln -s /home/pi/raspberry/graphite-api.yml /etc/graphite-api.yml
sudo ln -s /home/pi/rasberry/graphite_api /var/www/graphite_api
sudo a2enwsgi
sudo a2enmod headers

service apache2 restart
