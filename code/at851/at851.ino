#define __AVR_ATtiny841__
#include <Arduino.h>
#include <SoftwareSerial.h>
#include <TinyWireM.h>
#include <vector>
#include <string>
#include <algorithm>
#include <map>
using namespace std;

// This code is for the left ATTiny85
// +------+-----------------------+
// | PINS    | LABEL              |
// +------+-----------------------+
// | 1    | RESET(Not connected)  |
// | 2    | HC - 12 [3] TX        |
// | 3    | HC - 12 [3] RX        |
// | 4    | GND                   |
// | 5    | SDA                   |
// | 6    | HC - 12 [4] TX        |
// | 7    | SDK                   |
// | 8    | VCC                   |
// +------+-----------------------+
// https://ozh.github.io/ascii-tables/

// Function definitions
//      Message Handlers
//          LOCREQ
//              RXs an location request from the connected device and logs the position and time
//          SATCMD
//              Interfaces with the other components allowing inner network communication between the other nodes
//              and commands any changes to connected hardware
//          OTHER
//              Messages
//
//      Helping functions
//          sendI2C
//              Handles all I2C communication by sending data that is pushed to a buffer and sends it when the send conditions bool is true
//              sendingSAT/OM keeps teh transmittion open until it is complete
//          schedule
//              executes timed functions that are pushed into the scheduleVec vector in the format {time, function, args}
//          sendViaUart
//              Sends a string via uart
//          split
//              splits a string
//          RandomString
//              make the user id

// Needed features
//      Cross talk between the other ATTiny
//

SoftwareSerial HC12(3, 2); // (RX, TX)

// TinyWire Presets
const byte SLAVE_ADDR_MAIN = 100;
const byte SLAVE_ADDR_SAT = 200;
const byte SLAVE_ADDR_OM = 300;
boolean slaveSATPresent = false;
boolean slaveOMPresent = false;
unsigned long timeNow;
boolean sendingSAT = false;
boolean sendingOM = false;
boolean messagesReceived = false;
vector<uint8_t> receivedBytes;

// Schedule tracking
vector<vector<variant<unsigned long, void (*sendUART)(string), string>>> scheduleVec;

// This will be used to buffer messages that will be sent on the I2C bus
vector<string> I2CBuffer;

boolean sendSATCOND = false;
boolean sendOMCOND = false;

// last location
string lastLOC = "undefined";

// This sats id
string myId = "sat1";

// Map containing all the users
// JSON example
// {
//     "10digitID": [
//         "utctimestap",
//         "position",
//         etc...
//     ]
// }
map<string, vector<string>> users;

// I2C master reference
// https://github.com/nadavmatalon/TinyWireM/blob/master/examples/TinyWireM_example/ATtiny841_Master/ATtiny841_Master.ino

void setup()
{
    HC12.begin(9600);
    TinyWireM.begin(SLAVE_ADDR_MAIN);
    timeNow = millis();

    sendViaUART("LOCREQ+" + myId);
}

void loop()
{
    int advailableBytes = HC12.available();
    char msg[advailableBytes];
    int delimIndex;
    int delimIndex2;

    if (advailableBytes)
    {
        // Read the string from the serial connection
        for (int i = 0; i < advailableBytes; i++)
        {
            msg[i] = HC12.read();
            // Look for the + that denotes a command then note its index
            if (msg[i] == "+")
            {
                delimIndex = i;
            }
        }

        string tag;
        // Convert the char array to a string for furture processing
        for (int i = 0; i < delimIndex; i++)
        {
            tag += msg[i];
        }

        // Route the msg according to the command tag, if no command tag or an invalid
        // command tag treat it as another message
        switch (tag)
        {
        case tag == "LOCREQ":
            LOCREQ(msg);
            break;

        case tag == "SATCMD":
            SATCMD(msg);
            break;

        default:
            OTHER(msg);
            break;
        }
    }

    // Send and data buffered for the I2C bus
    sendI2C();
    // Run the schedule
    schedule();

    // Check how many bytes are waiting to be received
    uint8_t numBytes = TinyWireM.advailable();
    // if data is advailable
    if (numBytes > 0)
    {
        // let everyone know there are messages
        messagesReceived = true;
        string data;
        // append the data to the last vector item
        for (int i = 0; i < numBytes; i++)
        {
            data = TinyWireM.receive();
            receivedBytes[(receivedBytes.length() - 1) || 0]
                .push_back(data);
            if (data == "+")
            {
                delimIndex2 = i;
            }
        }

        string tag2;
        // Convert the char array to a string for furture processing
        for (int i = 0; i < delimIndex2; i++)
        {
            tag2 += data[i];
        }
        // Commands handled from the I2C bus
        switch (tag2)
        {
        case tag2 == "POSUPDATE":
            SETPOS(data);
            break;
        default:
            break;
        }
    }
}

void LOCREQ(string msg)
{
    // An LOCREQ message will be in the following format
    // LOCREQ+SATID USERID UTCTIMESTAMP

    // TODO:
    //       RX LOCREQ
    //       Store POS
    //       Send CHECKNET+
    //       RX CHECKNET+ and reply

    // returns {"USERID", "UTCTIMESTAMP"}
    vector<string> parsedLOCREQ = split(msg.substr(msg.find("+") + 1), " ");

    // Check if user is stored
    if (!users[parseLOQREQ[0]])
    { // user is not stored

        // jsut this code needs to stay
        I2CBuffer.push_back("CHECKNET+" + parsedLOCREQ[0]);
        sendSATCOND = true;
        // this need to be ran after the CHECKNET+ command gets a responce
        string id = RandomString(10);
        users.insert(pair<string, vector<string>>{id, {}});
        // UTCTIMESTAMP
        users[id].push_back(parsedLOCREQ[1]);
        // Position
        users[id].push_back(lastLOC);
    }
    else
    { // user is stored
        // message has already been relayed by the bridged connection
        // now we need to store the location
        // UTCTIMESTAMP
        users[parseLOQREQ[0]].push_back(parsedLOCREQ[1]);
        // Position
        users[parseLOQREQ[0]].push_back(lastLOC);
        float postion = calcOrbitExit(parseLOQREQ[0]);
        // send location to user
        // POSIT+satID userID %ofOrbitLeft
        scheduleVec.push_back({millis(), sendViaUART, "POSIT+" + myId + " " + parseLOQREQ[0] + " " + to_string(position)});
    }

    // Add the GETPOS+ command to the que
    I2Cbuffer.push_back("GETPOS+");
    // let the sendI2C function know to start sending to the OM
    sendOMCOND = true;
    // Schedule an location request via uart 50 seconds in the future
    scheduleVec.push_back({millis() + 50000, sendViaUART, "LOCREQ+" + myId});
}

void SATCMD(string msg)
{
    I2CBuffer.push_back("message");
    sendSATCOND = true;
    // or
    sendOMCOND = true;
}

void OTHER(string msg)
{
    // FROM userId TO otherUserId message
    vector<string> parsed = split(msg, " ");
    if (users[parsed[3]])
    {
        // if the user has connected check if they are out of range
        // we dont care if the user is in range because the message would have been automatically retransmitted
        float pos = calcOrbitExit(parsed[3]);
        if (pos <= 0 && pos >= 100)
        {
            // user is not in range
            // ask net work if they reply we will have to reroute the message
            I2CBuffer.push_back("CHECKNET+" + parsedLOCREQ[0]);
            sendSATCOND = true;
        }
    }
    else
    {
        // user is not stored
        // ask net work if they reply we will have to reroute the message
        I2CBuffer.push_back("CHECKNET+" + parsedLOCREQ[0]);
        sendSATCOND = true;
    }
}

void SETPOS(string data)
{
    // {Degress to the sun, % of orbit complete}
    lastLOC = data.substr(data.find("+") + 1);
}

// This function will send any message in the buffer to the correct "slave" I2C one byte at a time
void sendI2C()
{
    if (millis() - timeNow >= 500)
    {
        // Make sure the slaves are connected
        if (!slaveSATPresent)
        {                                                // determine if slave joined the I2C bus
            TinyWireM.beginTransmission(SLAVE_ADDR_SAT); // begin call to slave
            if (TinyWireM.endTransmission() == 0)
                slaveSATPresent = true; // if responds - mark slave as present
        }
        else if (!slaveOMPresent)
        {                                               // determine if slave joined the I2C bus
            TinyWireM.beginTransmission(SLAVE_ADDR_OM); // begin call to slave
            if (TinyWireM.endTransmission() == 0)
                slaveOMPresent = true; // if responds - mark slave as present
        }
        else
        {
            if (sendSATCOND)
            {
                string word = I2CBuffer[0];
                string letter = word[0];

                // This is a safety check to make sure we aren't indexing an empty element
                if (letter.length() != 0)
                {
                    // remove the first char for the next round
                    I2CBuffer[0].erase(I2CBuffer[0].begin());
                }
                else
                {
                    I2CBuffer.erase(I2CBuffer.begin());
                    word = I2CBuffer[0];
                    letter = word[0];
                    // remove the first char for the next round
                    I2CBuffer[0].erase(I2CBuffer[0].begin());
                }

                // slave found on I2C bus
                if (!sendingSAT)
                {
                    TinyWireM.beginTransmission(SLAVE_ADDR_SAT); // begin call to slave
                    sendingSAT = true;
                }
                TinyWireM.write(letter); // send a single byte to slave

                // Once all the data has been sent terminate the send condition
                if (I2CBuffer.length() == 0)
                {
                    sendSATCOND = false;
                    sendingSAT = false;
                    TinyWireM.endTransmission(); // end call to slave
                }
            }
            else if (sendOMCOND)
            {
                string word = I2CBuffer[0];
                string letter = word[0];

                // This is a safety check to make sure we aren't indexing an empty element
                if (letter.length() != 0)
                {
                    // remove the first char for the next round
                    I2CBuffer[0].erase(I2CBuffer[0].begin());
                }
                else
                {
                    I2CBuffer.erase(I2CBuffer.begin());
                    word = I2CBuffer[0];
                    letter = word[0];
                    // remove the first char for the next round
                    I2CBuffer[0].erase(I2CBuffer[0].begin());
                }

                // slave found on I2C bus
                if (!sendingOM)
                {
                    TinyWireM.beginTransmission(SLAVE_ADDR_OM); // begin call to slave
                    sendingOM = true;
                }
                TinyWireM.write(letter); // send a single byte to slave

                // Once all the data has been sent terminate the send condition
                if (I2CBuffer.length() == 0)
                {
                    sendOMCOND = false;
                    sendingOM = false;
                    TinyWireM.endTransmission(); // end call to slave
                }
            }
        }
        timeNow = millis(); // mark current time (in mS)
    }
}

void schedule()
{
    // scheduleVec is a vector that holds arrays that contain when you want to execute an action then the action and the arg
    for (int i = 0; i < scheduleVec.length(); i++)
    {
        if (millis() >= scheduleVec[i][0])
        {
            scheduleVec[i][1](scheduleVec[i][2]);
            // remove once ran
            scheduleVec[0].erase(scheduleVec[0].begin());
        }
    }
}

void sendViaUART(string msg)
{
    HC12.write(msg);
}

vector<string> split(string to_split, string delimiter)
{
    size_t pos = 0;
    vector<string> matches{};
    do
    {
        pos = to_split.find(delimiter);
        int change_end;
        if (pos == string::npos)
        {
            pos = to_split.length() - 1;
            change_end = 1;
        }
        else
        {
            change_end = 0;
        }
        matches.push_back(to_split.substr(0, pos + change_end));

        to_split.erase(0, pos + 1);

    } while (!to_split.empty());
    return matches;
}

string RandomString(int len)
{
    string str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    string newstr;
    int pos;
    while (newstr.size() != len)
    {
        pos = ((rand() % (str.size() - 1)));
        newstr += str.substr(pos, 1);
    }
    return newstr;
}

float calcOrbitExit(string id)
{
    // first find where we are in the orbit using time
    // then find the smallest position and the largest
    // calc percent of orbit complete
    float minV = 101;
    float maxV = 0;

    if (users[id])
    {
        // step by 2 because users alternates time and position
        for (int i = 0; i < users[id].length(); i += 2)
        {
            float pos = stof(users[i + 1]);
            if (pos > maxV)
            {
                maxV = pos;
            }
            else if (pos < minV)
            {
                minV = pos;
            }
        }

        float ourPos = stof(lastLOC.substr(lastLOC.find("+") + 1));

        // we will return percent complete of orbit fly over
        // if its out of range we will put a 0 or 100 depending if we are > or <
        // 0,0,0,0,0,0,1,2,3,4,5....,99,100,100,100,100...0,0,0,0,0,1,2,3...99,100,100...etc
        return max(min((ourPos - minV) / maxV), 100, 0)
    }
}
