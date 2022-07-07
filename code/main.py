import _thread
from machine import ADC
from getpos import POS
from uart import UART
from nonmain import *
import time

# get baselines
baselines = []
baselines[0] = ADC(18) # ADC_0
baselines[1] = ADC(19) # ADC_1

pos = POS(baselines)

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

# core0 handles the ground station and node to node
def uart14():
    u1Data = uart1.rx()
    u4Data = uart4.rx()
    # requirements
    # - NETCHECK+
    # - SATCMD+
    # - Switch users to use 2 or 3 on connect
    # - awaitingMessages

# core1 handles the data relay for the users
def uart23():
    u2Data = uart2.rx()
    u3Data = uart3.rx()

    # check if we are able to get locations
    cPos = pos.get()
    # main message handling logic
    messageControler(u2Data, cPos, uart2)
    messageControler(u3Data, cPos, uart3)

    # Make a LOCREQ+ every 35 minutes
    if cPos:
        if time.ticks_ms()-lastLOQREQ > 2.1e+6:
            uart2.tx("LOCREQ+")
            uart3.tx("LOCREQ+")
            lastLOQREQ = time.ticks_ms()

    # clean the user list and message que every cycle
    users = cleanUsers(users)
    awaitingMessages = cleanAwaitMsg(awaitingMessages)

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
                        "quedTime": time.ticks_ms()
                    })
    else:
        # get the request keys to find the command to run
        uKey = uData[0:uData.find("+")]
        uValues = uData[uData.find("+")+1:].split(" ")

        # when a LOCREQ is received we are getting a responce from a LOCREQ we sent out
        # An LOCREQ message will be in the following format
        # LOCREQ+SATID USERID UTCTIMESTAMP
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
                else:
                    # create user
                    users[uValues[1]] = {
                        "checkin": time.ticks_ms(),
                        "locationList": [] 
                    }
                    if cPos:
                        # if so then add the location to the location list
                        users[uValues[1]].locationList.append(cPos)

# this will run each task like a arduino program
def core0_task():
    while True:
        uart14()

def core1_task():
    while True:
        uart23()

# start the cores
_thread.start_new_thread(core1_task, ())
core0_task()