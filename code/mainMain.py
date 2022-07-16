import _thread
from machine import ADC
from lib.getpos import POS
from lib.uart import UART
from lib.nonmain import *
import time
import random

# get baselines
baselines = []
baselines.append(ADC(26).read_u16()) # ADC_0
baselines.append(ADC(27).read_u16()) # ADC_1

pos = POS(baselines)

# All should have a fixed freq
uart1 = UART(1200,2,3,0) # Ground station
uart2 = UART(1200,6,7,1) # Dynamic tasking
uart3 = UART(1200,10,11,2) # Dynamic tasking
uart4 = UART(1200,14,15,3) # Node to node

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

# core0 handles the ground station and node to node
def uart14():
    u1Data = uart1.rx()
    u4Data = uart4.rx()

    # check if we are able to get locations
    # cPos = pos.get()
    cPos = 50
    # main message handling logic
    if u1Data:
        messageControler(u1Data, cPos, uart1)
    if u4Data:
        messageControler(u4Data, cPos, uart4)

# core1 handles the data relay for the users
def uart23():
    global lastCleaning
    global users
    global usersOn2
    global usersOn3
    global awaitingMessages
    global lastLOQREQ

    u2Data = uart2.rx()
    u3Data = uart3.rx()

    # check if we are able to get locations
    # cPos = pos.get()
    cPos = 50
    # main message handling logic
    if u2Data:
        print("u2 data rxd")
        print(u2Data)
        messageControler(u2Data, cPos, uart2)
    if u3Data:
        print("u3 data rxd")
        print(u3Data)
        messageControler(u3Data, cPos, uart3)

    # Make a LOCREQ+ every 35 minutes
    # if cPos:
    #     if time.ticks_ms()-lastLOQREQ > 2.1e+6:
    #         uart2.tx("LOCREQ+"+mySatID)
    #         uart3.tx("LOCREQ+"+mySatID)
    #         lastLOQREQ = time.ticks_ms()

    # clean the user list and message que every 10 minutes
    if time.ticks_ms()-lastCleaning > 600000:
        users, usersOn2, usersOn3 = cleanUsers(users, usersOn2, usersOn3)
        awaitingMessages = cleanAwaitMsg(awaitingMessages)
        lastCleaning = time.ticks_ms()

def messageControler(uData, cPos ,uartParam):
    global users
    global usersOn2
    global usersOn3
    global awaitingMessages
    uKey = False
    uValues = False
    # echo the messge if no command is found
    if uData.find("+") == -1:
        # check if there is data
        if uData:
            # OTHER type message
            # FROM TO msg
            uArgs = uData.split(" ")
            # check if user is on local storage
            if uArgs[1] in users:
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
        print(uKey,uValues)
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
                    cleanMsg = " ".join(uData.split(" ")[2:])
                    uart2.tx(cleanMsg)
                if users[uValues[2]].freq == 3:
                    # just send the FROM TO msg
                    cleanMsg = " ".join(uData.split(" ")[2:])
                    uart3.tx(cleanMsg)
        elif uKey == "CONNECT":
            # CONNECT+randomToken
            # generate random id
            ID = randArr()

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
                "freq": freeDevice,
                "token": uValues[0]
            }
            if cPos:
                # if so then add the location to the location list
                users[ID]["locationList"].append(cPos)
            # reply to the user which device and what ID to use identifing them with the token they made
            # CONNECT+token freeDevice ID
            print(f"CONNECT+{uValues[0]} {freeDevice} {ID}")
            time.sleep(1)
            # uart1.tx(f"XYZ")
            uart1.tx(f"CONNECT+{uValues[0]} {freeDevice} {ID}")
        elif uKey == "SETID":
            # SETID+token id newId
            # check if use exists
            if users[uValues[1]]:
                #  check if token matches
                if users[uValues[0]].token == uValues[0]:
                    # change the key
                    users[uValues[2]] = users.pop(uValues[1])
# this will run each task like a arduino program
def core0_task():
    i = 0
    while i < 200:
        uart14()
        time.sleep(0.1)
        i += 1

def core1_task():
    i = 0
    while i < 200:
        uart23()
        time.sleep(0.1)
        i += 1

# start the cores
_thread.start_new_thread(core1_task, ())
core0_task()