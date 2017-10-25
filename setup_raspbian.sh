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

# /etc/graphite-api.yml
# search_index: /var/lib/graphite/index
# finders:
  # - graphite_api.finders.whisper.WhisperFinder
# functions:
  # - graphite_api.functions.SeriesFunctions
  # - graphite_api.functions.PieFunctions
# whisper:
  # directories:
    # - /var/lib/graphite/whisper
# carbon:
  # hosts:
    # - 127.0.0.1:7002
  # timeout: 1
  # retry_delay: 15
  # carbon_prefix: carbon
  # replication_factor: 1

apt-get install libapache2-mod-wsgi

# /var/www/wsgi-scripts/graphite-api.wsgi
# from graphite_api.app import app as application

/etc/apache2/sites-available/graphite.conf

# # /etc/apache2/sites-available/graphite.conf
# LoadModule wsgi_module modules/mod_wsgi.so
# WSGISocketPrefix /var/run/wsgi
# Listen 8013
# <VirtualHost *:8013>

 # WSGIDaemonProcess graphite-api processes=5 threads=5 display-name='%{GROUP}' inactivity-timeout=120
 # WSGIProcessGroup graphite-api
 # WSGIApplicationGroup %{GLOBAL}
 # WSGIImportScript /var/www/wsgi-scripts/graphite-api.wsgi process-group=graphite-api application-group=%{GLOBAL}

 # WSGIScriptAlias / /var/www/wsgi-scripts/graphite-api.wsgi

 # <Directory /var/www/wsgi-scripts/>
 # Order deny,allow
 # Allow from all
 # </Directory>
 # </VirtualHost>

ln -s ../sites-available/graphite.conf .
service apache2 restart
