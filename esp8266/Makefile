deploy: 
	sudo pkill picocom; sudo ampy --port /dev/ttyUSB0 put main.py /main.py;
deploy_and_relay: 
	sudo pkill picocom; sudo ampy --port /dev/ttyUSB0 put main_and_relay.py /main.py;
deploy_utils: 
	sudo pkill picocom; sudo ampy --port /dev/ttyUSB0 rmdir /utils; sudo ampy --port /dev/ttyUSB0 put utils /utils;
deploy_config: 
	sudo pkill picocom; sudo ampy --port /dev/ttyUSB0 put config.json /config.json;
	# sudo pkill picocom; sudo ampy --port /dev/ttyUSB0 put x /config.json;
deploy_static: 
	gzip -k -9 -f index.html;
	sudo ampy --port /dev/ttyUSB0 put index.html.gz /index.html.gz;
	# sudo ampy --port /dev/ttyUSB0 put favicon.ico /favicon.ico;
	sudo pkill picocom; sudo ampy --port /dev/ttyUSB0 put jquery.js.gz /jquery.js.gz; 
ls:
	sudo pkill picocom; sudo ampy --port /dev/ttyUSB0 ls
run:
	sudo pkill picocom; sudo picocom /dev/ttyUSB0 -b115200;
log:
	sudo pkill picocom; \
	sudo ampy --port /dev/ttyUSB0 get /main.log >> main.log && \
	sudo ampy --port /dev/ttyUSB0 rm /main.log;
	tail main.log
deploy_micropython:
	# http://micropython.org/resources/firmware/esp8266-20170823-v1.9.2.bin
	sudo pkill picocom; \
	sudo esptool.py --port /dev/ttyUSB0 erase_flash; \
	sudo esptool.py --port /dev/ttyUSB0 --chip esp8266 --baud 460800 write_flash --flash_size=4MB-c1 -fm dio 0 esp8266-20180511-v1.9.4.bin;
