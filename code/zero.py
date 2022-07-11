import serial
from time import sleep
from artic import *

ser = serial.Serial ("/dev/ttyS0", 1200)
# sudo od -t x1 -t a /dev/ttyS0
# sudo minicom -D /dev/ttyAMA0 --baudrate 1200
artic = ARTIC(ser.write,ser.read)

str = "hello dude"
artic.tx("TODI",str)