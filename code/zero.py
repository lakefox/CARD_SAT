import serial
from time import sleep
from artic import *

ser = serial.Serial ("/dev/ttyS0", 1200, timeout=0)
# sudo od -t x1 -t a /dev/ttyS0
# sudo minicom -D /dev/ttyAMA0 --baudrate 1200
artic = ARTIC(ser.write,ser.read)

i = 0
while i < 200:
    artic.rx()
    print(i)
    sleep(0.3)
    i += 1

# str = "hello dude"
# artic.tx("TODI",str)