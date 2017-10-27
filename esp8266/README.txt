http://micropython.org/resources/firmware/esp8266-20170823-v1.9.2.bin
sudo pip install esptool ampy -U
sudo apt-get install picocom
sudo esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect 0 esp8266-20170823-v1.9.2.bin 
sudo picocom /dev/ttyUSB0 -b115200
sudo ampy --port /dev/ttyUSB0 ls
sudo ampy --port /dev/ttyUSB0 put main.py /main.py
sudo ampy --port /dev/ttyUSB0 put config.json /config.json
