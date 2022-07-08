import _thread
from machine import ADC
from getpos import POS
from uart import UART
from nonmain import *
import time
import random
# Example using PIO to create a UART TX interface
from rp2 import PIO, StateMachine, asm_pio

# get baselines
baselines = []
baselines[0] = ADC(18) # ADC_0
baselines[1] = ADC(19) # ADC_1

pos = POS(baselines)

# All should have a fixed freq
uart1 = UART(9600,2,3,0) # Ground station
uart2 = UART(9600,6,7,1) # Dynamic tasking
uart3 = UART(9600,10,11,2) # Dynamic tasking
uart4 = UART(9600,14,15,3) # Node to node

# store for all the users connected
users = {}

# timestamp for when the last LOQREQ+ command was sent
lastLOQREQ = 0

# this satillite id
mySatID = "1234"

# que for messages that might need to be sent with the NETCHECK+
awaitingMessages = []

# stores the last time the users and awaiting messages were cleaned out
lastCleaning = 0

# used to track who is connected to what
usersOn2 = 0
usersOn3 = 0

# alphabet for id generation
alphabet = string.ascii_letters + string.digits

# core0 handles the ground station and node to node
def uart14():
    u1Data = uart1.rx()
    u4Data = uart4.rx()

    # check if we are able to get locations
    cPos = pos.get()
    # main message handling logic
    if u1Data:
        messageControler(u1Data, cPos, uart1)
    if u4Data:
        messageControler(u4Data, cPos, uart4)

# core1 handles the data relay for the users
def uart23():
    u2Data = uart2.rx()
    u3Data = uart3.rx()

    # check if we are able to get locations
    cPos = pos.get()
    # main message handling logic
    if u2Data:
        messageControler(u2Data, cPos, uart2)
    if u3Data:
        messageControler(u3Data, cPos, uart3)

    # Make a LOCREQ+ every 35 minutes
    if cPos:
        if time.ticks_ms()-lastLOQREQ > 2.1e+6:
            uart2.tx("LOCREQ+"+mySatID)
            uart3.tx("LOCREQ+"+mySatID)
            lastLOQREQ = time.ticks_ms()

    # clean the user list and message que every 10 minutes
    if time.ticks_ms()-lastCleaning > 600000:
        users = cleanUsers(users)
        awaitingMessages = cleanAwaitMsg(awaitingMessages)
        lastCleaning = time.ticks_ms()

def messageControler(uData, cPos ,uartParam):
    uKey = False
    uValues = False
    # echo the messge if no command is found
    if uData.find("+") > -1:
        # check if there is data
        if uData:
            # OTHER type message
            # FROM TO msg
            uArgs = uData.split(" ")
            # check if user is on local storage
            if users[uArgs[1]]:
                # check if user is in foot print
                if userInFootPrint(users[uArgs[1]], cPos):
                    # if it is then transmit it down
                    uartParam.tx(uData)
                else:
                    # Ask the network if the user is on the network using tx 4
                    uart4.tx("NETCHECK+"+uArgs[1])
                    # add users message to a waiting list
                    awaitingMessages.append({
                        "data": uData,
                        "quedTime": time.ticks_ms(),
                        "TO": uArgs[1]
                    })
    else:
        # get the request keys to find the command to run
        uKey = uData[0:uData.find("+")]
        uValues = uData[uData.find("+")+1:].split(" ")

        # when a LOCREQ is received we are getting a responce from a LOCREQ we sent out
        # An LOCREQ message will be in the following format
        # LOCREQ+SATID USERID
        if uKey == "LOCREQ":
            # make sure the responce is to us
            if uValues[0] == mySatID:
                # check if user exists within our users list
                if users[uValues[1]]:
                    # update their checkin time
                    users[uValues[1]].checkin = time.ticks_ms()
                    if cPos:
                        # if so then add the location to the location list
                        users[uValues[1]].locationList.append(cPos)
        elif uKey == "NETCHECK":
            # request we are being asked to reply to
            # NETCHECK+satID userID
            # responce to a NETCHECK we asked
            # NETCHECK+mySatID theirSatID userID
            if uValues[0] == mySatID:
                # ask the node relay
                # RELAY+theirSatID FROM TO msg
                for msg in awaitingMessages:
                    # check each msg for the TO recepient
                    if msg.TO == uValues[2]:
                        uart4.tx(f"RELAY+{uValues[1]} {msg.data}")
                        awaitingMessages.remove(msg)
            else:
                # check if we have the user stored
                if users[uValues[1]]:
                    # check if user can be contacted
                    if userInFootPrint(users[uValues[1]], cPos):
                        # tell the node we have it
                        uart4.tx(f"NETCHECK+{mySatID} {uValues[0]} {uValues[1]}")
        elif uKey == "RELAY":
            # RELAY+mySatID FROM TO msg
            if uValues[0] == mySatID:
                if users[uValues[2]].freq == 2:
                    # just send the FROM TO msg
                    uart2.tx(" ".join(uData.split(" ")[2:]))
                if users[uValues[2]].freq == 3:
                    # just send the FROM TO msg
                    uart3.tx(" ".join(uData.split(" ")[2:]))
        elif uKey == "CONNECT":
            # CONNECT+randomToken
            # generate random id
            ID = ''.join(random.choice([chr(i) for i in range(ord('a'),ord('z'))]) for _ in range(10))
            idGood = False
            # generate ids until a new one is created
            while not idGood:
                if ID in users.keys():
                    ID = ''.join(random.choice([chr(i) for i in range(ord('a'),ord('z'))]) for _ in range(10))
                    idGood = True

            # keep track of devices
            freeDevice = 2
            if usersOn2 > usersOn3:
                freeDevice = 3
                usersOn3 += 1
            else: 
                usersOn2 += 1

            # create user
            users[ID] = {
                "checkin": time.ticks_ms(),
                "locationList": [],
                "freq": freeDevice
            }
            if cPos:
                # if so then add the location to the location list
                users[ID].locationList.append(cPos)
            # reply to the user which device and what ID to use identifing them with the token they made
            # CONNECT+token freeDevice ID
            uart1.tx(f"CONNECT+{uValues[0]} {freeDevice} {ID}")


# this will run each task like a arduino program
def core0_task():
    while True:
        uart14()

def core1_task():
    while True:
        uart23()

def cleanUsers(users):
    for user in users:
        if users[user].checkin:
            # check is user has checked in within 3 hours
            if time.ticks_ms()-users[user].checkin > 1.08e+7:
                # if not delete the user
                del users[user]

def userInFootPrint(user, cPos):
    minPos = 101
    maxPos = 0
    for userPos in user["locationList"]:
        if userPos < minPos:
            minPos = userPos
        elif userPos > maxPos:
            maxPos = userPos
    if cPos > minPos and cPos < maxPos:
        return True
    else:
        return False

def cleanAwaitMsg(awaitingMessages):
    for msg in awaitingMessages:
        # check if the qued time is greater than 10 minutes then delete it
        if time.ticks_ms()-msg["quedTime"] > 600000:
            awaitingMessages.remove(msg)
    return awaitingMessages

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


# uart1 = UART(9600,10,11,0)
# uart2 = UART(9600,6,7,2)
# uart3 = UART(9600,14,15,6)

# # Function for core1 to execute to write to the given UART.
# # def core1_task(uart, text):
# #     while (True):
# #         uart.tx(text)

# # # Print a different message from each UART

# # _thread.start_new_thread(core1_task, (uart3, "text"))

# while (True):
#     # uart1.tx("Hello from UART!\n")
#     t = uart1.rx()
#     if (t):
#         print(t)

# start the cores
_thread.start_new_thread(core1_task, ())
core0_task()