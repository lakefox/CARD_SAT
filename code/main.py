import _thread
from machine import ADC
from getpos import POS
from uart import UART
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

lastLOQREQ = 0

mySatID = "1234"

# core0 handles the ground station and node to node
def core0_task(uart1, uart4):
    u1Data = uart1.rx()
    u4Data = uart4.rx()

# core1 handles the data relay for the users
def core1_task(uart, text):
    u2Data = uart2.rx()
    u3Data = uart3.rx()

    # echo the messge if no command is found
    if u2Data.find("+") > -1:
        if u2Data:
            uart2.tx(u2Data)
    else:
        # get the request keys to find the command to run
        u2Key = u2Data[0:u2Data.find("+")]
        u2Values = u2Data[u2Data.find("+")+1:].split(" ")
    if u3Data.find("+") > -1:
        if u3Data:
            uart3.tx(u3Data)
    else:
        # get the request keys to find the command to run
        u3Key = u3Data[0:u3Data.find("+")]
        u3Values = u3Data[u3Data.find("+")+1:].split(" ")

    if u2Key:
        # An LOCREQ message will be in the following format
        # when a LOCREQ is received we are getting a responce from a LOCREQ we sent out
        # LOCREQ+SATID USERID UTCTIMESTAMP
        if u2Key == "LOCREQ":
            if u2Values[0] == mySatID:
                # check if user exists within our users list
                if users[u2Values[1]]:
                    # update their checkin time
                    users[u2Values[1]].checkin = time.ticks_ms()
                    # check if we are able to get locations
                    cPos = pos.get()
                    if cPos:
                        # if so then add the location to the location list
                        users[u2Values[1]].locationList.append(cPos)
                else:
                    # create user
                    users[u2Values[1]] = {
                        "checkin": time.time_ms(),
                        "locationList": [] 
                    }
                    # check if we are able to get locations
                    cPos = pos.get()
                    if cPos:
                        # if so then add the location to the location list
                        users[u2Values[1]].locationList.append(cPos)
    # make the above for 3


    # Make a LOCREQ+ every 35 minutes
    # check if we are able to get locations
    cPos = pos.get()
    if cPos:
        if time.time_ms()-lastLOQREQ > 2.1e+6:
            uart2.tx("LOCREQ+")
            uart3.tx("LOCREQ+")
            lastLOQREQ = time.time_ms()
            
    # clean the user list every cycle
    cleanUsers()

cores = [core0_task,core1_task]
for i in range(0,2):
    _thread.start_new_thread(cores[i], ())

def cleanUsers() {
    for user in users:
        if users[user].checkin:
            # check is user has checked in within 3 hours
            if time.ticks_ms()-users[user].checkin > 1.08e+7:
                # if not delete the user
                del users[user]
}