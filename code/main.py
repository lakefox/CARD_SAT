import _thread
from uart import UART

uart1 = UART(9600,10,11,0)
uart2 = UART(9600,6,7,2)
uart3 = UART(9600,14,15,6)

# Function for core1 to execute to write to the given UART.
def core1_task(uart, text):
    while (True):
        uart.tx(text)

# Print a different message from each UART

_thread.start_new_thread(core1_task, (uart3, "text"))

while (True):
    # uart1.tx("Hello from UART!\n")
    t = uart1.rx()
    if (t):
        print(t)