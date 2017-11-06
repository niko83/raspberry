deploy: 
	sudo pkill picocom ; \
	sudo ampy --port /dev/ttyUSB0 put main.py /main.py ; \
	(sudo ampy --port /dev/ttyUSB0 rmdir /utils 2> /dev/null || echo "/utils does not exists"); \
	sudo ampy --port /dev/ttyUSB0 put utils; \
	(sudo ampy --port /dev/ttyUSB0 rmdir /lib 2> /dev/null || echo "/lib does not exists"1) ; \
	sudo ampy --port /dev/ttyUSB0 put lib ; \
	sudo ampy --port /dev/ttyUSB0 put config.json /config.json;
ls:
	sudo pkill picocom; \
	echo '=====ROOT====='; \
	sudo ampy --port /dev/ttyUSB0 ls /;  \
	echo '=====utils====='; \
	sudo ampy --port /dev/ttyUSB0 ls /utils; \
	echo '=====lib====='; \
	sudo ampy --port /dev/ttyUSB0 ls /lib
run:
	sudo picocom /dev/ttyUSB0 -b115200;
log:
	sudo pkill picocom; \
	sudo ampy --port /dev/ttyUSB0 get /main.log;
