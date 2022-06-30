#define __AVR_ATtiny841__
#include <Arduino.h>
#include <TinyWireM.h>
#include <vector>
#include <string>
using namespace std;

// This code is for the Oreintation Module ATTiny85
// +------+-----------------------+
// | PINS    | LABEL              |
// +------+-----------------------+
// | 1    | RESET(Not connected)  |
// | 2    | HC-12 [3] TX          |
// | 3    | HC-12 [3] RX          |
// | 4    | GND                   |
// | 5    | SDA                   |
// | 6    | HC-12 [4] TX          |
// | 7    | SDK                   |
// | 8    | VCC                   |
// +------+-----------------------+
// https://ozh.github.io/ascii-tables/

// Function definitions
//      Message Handlers
//          GETPOS
//              Sends the direction of the satellite from the sun
//
//      Helping functions
//          schedule
//              executes timed functions that are pushed into the scheduleVec vector in the format {time, function, args}

SoftwareSerial HC12(3, 2); // (RX, TX)

// TinyWire Presets
const byte SLAVE_ADDR_MAIN = 100;
const byte SLAVE_ADDR_SAT = 200;
const byte SLAVE_ADDR_OM = 300;
boolean slaveSATPresent = false;
boolean slaveMAINPresent = false;
unsigned long timeNow;
boolean sendingSAT = false;
boolean sendingMAIN = false;
boolean messagesReceived = false;

set<uint8_t> receivedBytes;

// Schedule tracking
vector<unsigned long> scheduleVec;

// This will be used to buffer messages that will be sent on the I2C bus
vector<string> I2CBuffer;

boolean sendSATCOND = false;
boolean sendMAINCOND = false;

// I2C master reference
// https://github.com/nadavmatalon/TinyWireM/blob/master/examples/TinyWireM_example/ATtiny841_Master/ATtiny841_Master.ino

void setup()
{
    TinyWireM.begin(SLAVE_ADDR_OM);
    timeNow = millis();
    orbitTime = millis();

    baseline1 = analogRead(2);
    baseline2 = analogRead(3);
}

void loop()
{

    // Send and data buffered for the I2C bus
    sendI2C();
    // Run the schedule
    schedule();

    int advailableBytes = HC12.available();
    char msg[advailableBytes];
    int delimIndex;

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

    // During the first orbit record the max voltages of each pannel
    if (orbitTime - timeNow <= orbitCompleteTime)
    {
        float testV1 = analogRead(2);
        float testV2 = analogRead(3);

        // set maxV* to the max voltage we see
        if (testV1 > maxV1)
        {
            maxV1 = testV1;
        }
        if (testV2 > maxV2)
        {
            maxV2 = testV2;
        }
        // set maxV* to the min voltage we see
        if (testV1 < minV1)
        {
            minV1 = testV1;
        }
        if (testV2 < minV2)
        {
            minV2 = testV2;
        }
    }
    else
    {
        // Check if GETPOS+ is in the set
        if (receivedBytes.find("GETPOS+") != receivedBytes.end())
        {
            GETPOS();
            // Remove the command to clear the line
            receivedBytes.erase(0);
        }
    }
}

void GETPOS()
{
    updateVREF();
    float current1 = (baseline1 - vrefs[0]) / 0.1;
    float current2 = (baseline2 - vrefs[1]) / 0.1;

    infloatt volt1 = current1 * vref[3];
    float volt2 = current2 * vref[3];
    // using these two voltage measurements we will calculate the angle to the sun

    float posPercent;
    float pos;

    // posPercent is the percent between 180 and 0
    // volt1 in the front pannel volt2 is the back
    if (volt1 > volt2)
    {
        posPercent = (volt1 - minV1) / (maxV1 - minV1);
        pos = 180 * posPercent;
    }
    else
    {
        posPercent = (volt2 - minV2) / (maxV2 - minV2);
        pos = (180 * posPercent) * -1;
    }

    // Send pos immediately
    // POSUPDATE+90 5.334
    scheduleVec.push_back({millis(), sendMAIN, "POSUPDATE+" + to_string(pos) + " " + to_string((millis() / orbitCompleteTime) * 100)});
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

void updateVREF()
{
    vrefs[0] = analogRead(2);
    vrefs[1] = analogRead(3);
    vrefs[2] = analogRead(6);
}

void sendMAIN(msg)
{
    sendMAINCOND = true;
    I2CBuffer.push_back(msg);
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
        else if (!slaveMAINPresent)
        {                                                 // determine if slave joined the I2C bus
            TinyWireM.beginTransmission(SLAVE_ADDR_MAIN); // begin call to slave
            if (TinyWireM.endTransmission() == 0)
                slaveMAINPresent = true; // if responds - mark slave as present
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
                    TinyWireM.endTransmission(); // end call to slave
                }
            }
            else if (sendMAINCOND)
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
                if (!sendingMAIN)
                {
                    TinyWireM.beginTransmission(SLAVE_ADDR_MAIN); // begin call to slave
                    sendingMAIN = true;
                }
                TinyWireM.write(letter); // send a single byte to slave

                // Once all the data has been sent terminate the send condition
                if (I2CBuffer.length() == 0)
                {
                    sendMAINCOND = false;
                    TinyWireM.endTransmission(); // end call to slave
                }
            }
        }
        timeNow = millis(); // mark current time (in mS)
    }
}