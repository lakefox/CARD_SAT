import random

class Artic:
    def __init__(self, tx, rx) -> None:
        self.tx = tx
        self.rx = rx
        self.token = ''.join(random.choice([chr(i) for i in range(ord('a'),ord('z'))]) for _ in range(10))
        self.id = ""
        self.connect()
    def tx(self, data):
        self.tx(data+"\f")
    
    def rx(self):
        data = self.rx()

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
                        "data": " ".join(dArgs[2:])
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
                self.tx(f"LOCREQ+{dValues[0]} {self.id}")


    def connect(self):
        self.tx("CONNECT+"+self.token)

    def setChannel():
        print()