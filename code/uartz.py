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
def cleanData(data):
        newdata = []
        for i in data:
            if i != 0:
                newdata.append(i)
        return newdata
i = 0
while i < 300:
    print(cleanData(read()))
    # ser.read(10)
    i += 1