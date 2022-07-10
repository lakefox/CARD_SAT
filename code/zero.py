import serial
from time import sleep
from artic import *

ser = serial.Serial ("/dev/ttyS0", 1200)

artic = ARTIC(ser.write,ser.read)

str = "hello dude"
for i in range(0, int(len(str)/3)+1):
    print(str[i*3:(i*3)+3])
    artic.tx(str[i*3:(i*3)+3])
    sleep(0.3)