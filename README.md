#. Download  Raspbian and write Image
```
wget https://downloads.raspberrypi.org/raspbian_lite_latest -O /tmp/raspbian_lite.zip
unzip -p /tmp/raspbian_lite.zip | sudo dd of=/dev/sdb bs=4M status=progress conv=fsync

# check written image
unzip /tmp/raspbian_lite.zip
2017-11-29-raspbian-stretch-lite.img
sudo dd bs=4M if=/dev/sdb of=/tmp/from-sd-card.img
truncate --reference 2017-11-29-raspbian-stretch-lite.img from-sd-card.img
diff -s /tmp/from-sd-card.img 2017-11-29-raspbian-stretch-lite.img
```          

#. Plug Display and keyboard for enable SSHD 
```
loging: pi
password: raspberry
```
sudo raspi-config

#. Copy  public ssh key to raspberry
```
ssh-copy-id -i ~/.ssh/id_rsa.pub pi@192.168.100.12
```

#. Setup software:
```
passwd
sudo apt-get update
sudo apt-get upgrade -y
curl -sSL https://get.docker.com | sh
sudo curl -L https://github.com/docker/compose/releases/download/1.16.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
sudo +x /usr/local/bin/docker-compose
sudo usermod -aG docker pi

sudo apt-get install supervisor git vim python-pip
sudo mv /etc/supervisor/supervisord.conf /etc/supervisor/supervisord.conf_bak
sudo ln -s /home/pi/raspberry/supervisord.conf /etc/supervisor/pi.conf

git clone https://github.com/niko83/raspberry.git ~/raspberry

pip install docker-compose falcon paho-mqtt
echo "export PATH=home/pi/.local/bin:$PATH" >> ~/.bashrc

cd raspberry; docker-compose up

mkdir /home/pi/logs


sudo apt-get install python3-rpi.gpio ipython3  -y
sudo pip install pip -U
sudo pip install  supervisor 

```


```
sudo pip install docker-compose
sudo apt-get install python python-pip build-essential python-dev libcairo2-dev libffi-dev
```

```
docker pull tobi312/rpi-nginx
mkdir -p /home/pi/html && mkdir -p /home/pi/.config/nginx && touch /home/pi/.config/nginx/default.conf
docker run --name nginx -d -p 80:80 -p 443:443 --link some-php-fpm-container:phphost -v /home/pi/.ssl:/etc/nginx/ssl:ro -v /home/pi/.config/nginx:/etc/nginx/conf.d:ro -v /home/pi/html:/var/www/html tobi312/rpi-nginx
```

```
docker pull tobi312/rpi-nginx
mkdir -p /home/pi/html && mkdir -p /home/pi/.config/nginx && touch /home/pi/.config/nginx/default.conf
docker run --name nginx -d -p 80:80 -p 443:443 --link some-php-fpm-container:phphost -v /home/pi/.ssl:/etc/nginx/ssl:ro -v /home/pi/.config/nginx:/etc/nginx/conf.d:ro -v /home/pi/html:/var/www/html tobi312/rpi-nginx
```
