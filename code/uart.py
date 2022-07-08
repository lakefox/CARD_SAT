# Example using PIO to create a UART TX interface
from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
import time

@asm_pio(sideset_init=PIO.OUT_HIGH, out_init=PIO.OUT_HIGH, out_shiftdir=PIO.SHIFT_RIGHT)
def uart_tx():
    # Block with TX deasserted until data available
    pull()
    # Initialise bit counter, assert start bit for 8 cycles
    set(x, 7)  .side(0)       [7]
    # Shift out 8 data bits, 8 execution cycles per bit
    label("bitloop")
    out(pins, 1)              [6]
    jmp(x_dec, "bitloop")
    # Assert stop bit for 8 cycles total (incl 1 for pull())
    nop()      .side(1)       [6]

@asm_pio(
    in_shiftdir=rp2.PIO.SHIFT_RIGHT,
)
def uart_rx():
    # fmt: off
    label("start")
    # Stall until start bit is asserted
    wait(0, pin, 0)
    # Preload bit counter, then delay until halfway through
    # the first data bit (12 cycles incl wait, set).
    set(x, 7)                 [10]
    label("bitloop")
    # Shift data bit into ISR
    in_(pins, 1)
    # Loop 8 times, each loop iteration is 8 cycles
    jmp(x_dec, "bitloop")     [6]
    # Check stop bit (should be high)
    jmp(pin, "good_stop")
    # Either a framing error or a break. Set a sticky flag
    # and wait for line to return to idle state.
    irq(block, 4)
    wait(1, pin, 0)
    # Don't push data if we didn't see good framing.
    jmp("start")
    # No delay before returning to start; a little slack is
    # important in case the TX clock is slightly too fast.
    label("good_stop")
    push(block)
    # fmt: on

# The UART class creates two state machines, one for TX and one for RX. The TX state machine is fed
# characters to send, and the RX state machine is read for characters received if the termination charector
class UART:
    def __init__(self,UART_BAUD=9600,PIN_TX=10,PIN_RX=11, ID=0):
        self.UART_BAUD = UART_BAUD
        self.PIN_TX = PIN_TX
        self.PIN_RX = Pin(PIN_RX, Pin.IN, Pin.PULL_UP)
        print(self.UART_BAUD,self.PIN_TX,self.PIN_RX,ID)
        self.sm1 = StateMachine(
            ID*2,uart_tx,freq=8 * self.UART_BAUD, sideset_base=Pin(self.PIN_TX), out_base=Pin(self.PIN_TX)
        )
        self.sm1.active(1)

        self.sm2 = StateMachine(
            (ID*2)+1,
            uart_rx,
            freq=8 * self.UART_BAUD,
            in_base=self.PIN_RX,  # For WAIT, IN
            jmp_pin=self.PIN_RX,  # For JMP
        )
        self.sm2.active(1)
        # store each message in a buffer then as the loop asks for it just push the newest one
        self.messageBuffer = []

    # We can print characters from each UART by pushing them to the TX FIFO
    def tx(self, msg):
        for c in msg:
            self.sm1.put(ord(c))
        return 1;
    def rx(self):
        msg = ""
        retStr = ""
        for i in range(0,self.sm2.rx_fifo()):
            c = chr(self.sm2.get() >> 24)
            if c != "\f":
                self.messageBuffer += c
            else:
                retStr = self.messageBuffer[:]
        if retStr != "":
            return retStr
        else:
            return False


uart1 = UART(9600,10,11,0)
# uart2 = UART(9600,6,7,2)
# uart3 = UART(9600,14,15,6)

# # Function for core1 to execute to write to the given UART.
# # def core1_task(uart, text):
# #     while (True):
# #         uart.tx(text)

# # # Print a different message from each UART

# # _thread.start_new_thread(core1_task, (uart3, "text"))

while (True):
    uart1.tx("Hello from UART!\n")
    t = uart1.rx()
    if (t):
        print(t)