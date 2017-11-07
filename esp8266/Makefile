deploy: 
	echo "."; sudo pkill picocom ; \
	echo "."; sudo ampy --port /dev/ttyUSB0 put main.py /main.py ; \
	echo "."; (sudo ampy --port /dev/ttyUSB0 rmdir /utils 2> /dev/null || echo "/utils does not exist"); \
	echo "."; sudo ampy --port /dev/ttyUSB0 put utils; \
	echo "."; (sudo ampy --port /dev/ttyUSB0 rmdir /lib 2> /dev/null || echo "/lib does not exist") ; \
	echo "."; sudo ampy --port /dev/ttyUSB0 put lib ; \
	echo "."; sudo ampy --port /dev/ttyUSB0 put config.json /config.json;
ls:
	sudo pkill picocom; \
	echo '=====ROOT====='; \
	sudo ampy --port /dev/ttyUSB0 ls; \
	echo '=====utils====='; \
	sudo ampy --port /dev/ttyUSB0 ls /utils; \
	echo '=====lib====='; \
	sudo ampy --port /dev/ttyUSB0 ls /lib
run:
	sudo picocom /dev/ttyUSB0 -b115200;
log:
	sudo pkill picocom; \
	sudo ampy --port /dev/ttyUSB0 get /main.log;
deploy_micropython:
	sudo pkill picocom; \
	sudo esptool.py --port /dev/ttyUSB0 erase_flash; \
	sudo esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect -fm dio 0 esp8266-20171101-v1.9.3.bin;
