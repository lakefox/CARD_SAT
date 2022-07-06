from machine import UART

uart1 = UART(1, baudrate=9600)
uart1.init(9600, bits=8, parity=None, stop=1, flow=UART.RTS | UART.CTS) # init with given parameters
while (True):
    uart1.write('hello\n')  # write 5 bytes
    print("hello")