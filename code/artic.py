import random

class Artic:
    def __init__(self, txf, rxf) -> None:
        self.txf = txf
        self.rxf = rxf
        self.token = ''.join(random.choice([chr(i) for i in range(ord('a'),ord('z'))]) for _ in range(10))
        self.id = ""
        self.connect()
    def tx(self,TO, data):
        if self.id != "":
            self.txf(f"{self.id} {TO} {data}\r")
        else:
            return False
    
    def rx(self):
        data = self.rxf()
        error = False
        errMsg = False

        # cut out the add number of spaces
        verifyNum = ord(data[data.rfind(" ")+1:data.rfind("\n")])
        # remove the end of the data
        data = data[0:data.rfind(" ")]
        # count the spaces
        spaceCount = data.count(" ")

        # let the user know there was an error
        if verifyNum != spaceCount:
            error = True
            errMsg = "Data transmission error."
            

        dKey = False
        dValues = False
        # echo the messge if no command is found
        if data.find("+") > -1:
            # check if there is data
            if data:
                # OTHER type message
                # FROM TO msg
                dArgs = data.split(" ")
                # check if message is to you
                if dArgs[1] == self.id:
                    return {
                        "from": dArgs[0],
                        "data": " ".join(dArgs[2:]),
                        "error": error,
                        "error_message": errMsg
                    } 
                
        else:
            # get the request keys to find the command to run
            dKey = data[0:data.find("+")]
            dValues = data[data.find("+")+1:].split(" ")

            if dKey == "CONNECT":
                # CONNECT+token channel ID
                if dValues[0] == self.token:
                    self.id = dValues[2]
                    self.setChannel(dValues[1])

            elif dKey == "LOCREQ":
                # An LOCREQ message will be in the following format
                # LOCREQ+SATID
                # Responce
                # LOCREQ+SATID USERID
                self.txf(f"LOCREQ+{dValues[0]} {self.id}\r")


    def connect(self):
        self.txf(f"CONNECT+{self.token}\r")

    def setChannel():
        print()
    
    def getId(self):
        return self.id

    def setId(self, newId):
        # you can set an id your self but only after you have connected and you have to pass your token 
        # for a little more security
        if self.id != "":
            self.txf(f"SETID+{self.token} {self.id} {newId}\r")
            self.id = newId