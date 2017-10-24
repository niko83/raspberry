# ssh-copy-id -i ~/.ssh/id_rsa.pub pi@192.168.100.12
passwd
sudo apt-get update
sudo apt-get upgrade -y
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker pi
sudo apt-get install vim python3-rpi.gpio ipython3 -y

