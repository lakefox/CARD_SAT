import random
from time import sleep

class ARTIC:
    def __init__(self, txf, rxf):
        self.txf = txf
        self.rxf = rxf
        self.token = ''.join(random.choice([chr(i) for i in range(ord('a'),ord('z'))]) for _ in range(10))
        self.id = "123"
        self.termLen = 5
        # self.connect()

    def connect(self):
        self.txSlow(f"CONNECT+{self.token}")

    def tx(self,TO, data):
        if self.id != "":
            self.txSlow(f"{self.id} {TO} {data}")
        else:
            return False

    def txSlow(self, msg):
        term = self.randArr()
        m = bytes(f"{term} {msg} {term}",'utf8')
        # print(m)
        for i in range(0, int(len(m)/3)+1):
            self.txf(m[i*3:(i*3)+3])
            sleep(0.3)

    def rx(self):
        data = self.rxf()

        #if data != b'':
        print(self.cleanData(data))
        # print(ord(data))
        # print(chr(ord(data)))
        dKey = False
        dValues = False
        # echo the messge if no command is found
        # if data.find("+") > -1:
        #     # check if there is data
        #     if data:
        #         # OTHER type message
        #         # FROM TO msg
        #         dArgs = data.split(" ")
        #         # check if message is to you
        #         if dArgs[1] == self.id:
        #             return {
        #                 "from": dArgs[0],
        #                 "data": " ".join(dArgs[2:])
        #             }
        # else:
        #     # get the request keys to find the command to run
        #     dKey = data[0:data.find("+")]
        #     dValues = data[data.find("+")+1:].split(" ")

        #     if dKey == "CONNECT":
        #         # CONNECT+token channel ID
        #         if dValues[0] == self.token:
        #             self.id = dValues[2]
        #             self.setChannel(dValues[1])

        #     elif dKey == "LOCREQ":
        #         # An LOCREQ message will be in the following format
        #         # LOCREQ+SATID
        #         # Responce
        #         # LOCREQ+SATID USERID
        #         term = self.randArr()
        #         self.txSlow(f"LOCREQ+{dValues[0]} {self.id} {term}")

    def setChannel(self):
        print()
    
    def getId(self):
        return self.id

    def setId(self, newId):
        # you can set an id your self but only after you have connected and you have to pass your token 
        # for a little more security
        if self.id != "":
            self.txSlow(f"SETID+{self.token} {self.id} {newId}")
            self.id = newId
    
    def randArr(self):
        return ''.join(random.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) for _ in range(self.termLen))

    def cleanData(self, data):
        newdata = []
        for i in data:
            if i != 0:
                newdata.append(i)
        return newdata