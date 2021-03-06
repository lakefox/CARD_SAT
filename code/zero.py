import serial
from time import sleep
from artic import *

ser = serial.Serial ("/dev/serial0", 1200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
# sudo od -t x1 -t a /dev/ttyS0
# sudo minicom -D /dev/ttyS0 --baudrate 1200
def read():
    rx_data = ser.read()
    print(rx_data)
    sleep(0.03)
    data_left = ser.inWaiting()
    rx_data += ser.read(data_left)
    return rx_data

artic = ARTIC(ser.write,read)

i = 0
while i < 300:
    artic.rx()
    i += 1

# str = "hello dude"
# artic.tx("TODI",str)