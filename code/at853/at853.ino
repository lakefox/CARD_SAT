#define __AVR_ATtiny841__
#include <Arduino.h>
#include <TinyWireM.h>
#include <vector>
#include <string>
#include <set>
using namespace std;

// This code is for the Oreintation Module ATTiny85
// +------+-----------------------+
// | PINS    | LABEL              |
// +------+-----------------------+
// | 1    | RESET(Not connected)  |
// | 2    | VREF 1 ADC_0          |
// | 3    | VREF 2 ADC_1          |
// | 4    | GND                   |
// | 5    | SDA                   |
// | 6    | VREF 3 ADC_2          |
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

// https://electronics.stackexchange.com/questions/624662/how-to-measure-the-power-of-two-small-solar-panels-independently-and-combine-the?noredirect=1#comment1650531_624662

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
vector<vector<variant<unsigned long, void (*sendUART)(string), string>>> scheduleVec;

// This will be used to buffer messages that will be sent on the I2C bus
vector<string> I2CBuffer;

boolean sendSATCOND = false;
boolean sendMAINCOND = false;

// vref presets
int baseline1 = 0;
int baseline2 = 0;
float vrefs[3] = {0, 0, 0};

// voltage presets
int maxV1 = 0;
int maxV2 = 0;
int minV1 = 255;
int minV2 = 255;
int orbitTime = 0;
int orbitCompleteTime = 7680000;

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
    // Update the time
    orbitTime = millis();

    // Check how many bytes are waiting to be received
    uint8_t numBytes = TinyWireM.advailable();
    // if data is advailable
    if (numBytes > 0)
    {
        // let everyone know there are messages
        messagesReceived = true;
        // append the data to the last vector item
        for (int i = 0; i < numBytes; i++)
        {
            receivedBytes[(receivedBytes.length() - 1) || 0].insert(TinyWireM.receive());
        }

        // Check if GETPOS+ is in the set
        if (receivedBytes.find("GETPOS+") != receivedBytes.end())
        {
            GETPOS()
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

    float volt1 = current1 * vref[3];
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
    // Estimated degrees to the sun

    // Add 180 to bring pos to a 360 then get percent
    float posPercent = (pos + 180) / 360;

    // percent of orbit complete in time from peak light
    float timePercent = (millis() / orbitCompleteTime) * 100;

    // Get the average of the estimated percents
    float avgPercent = (posPercent + timePercent) / 2;

    float avgDeg = 360 * avgPercent;
    // POSUPDATE+degs
    scheduleVec.push_back({millis(), sendMAIN, "POSUPDATE+" + to_string(avgDeg)});
}

// This is a function that will execute a function at a specific time.
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

// This function is updating the vrefs array with the current voltage readings from the solar panels.
void updateVREF()
{
    vrefs[0] = analogRead(2);
    vrefs[1] = analogRead(3);
    vrefs[2] = analogRead(6);
}

void sendMAIN(string msg)
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
                    sendingSAT = false;
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
                    sendingMAIN = false;
                    TinyWireM.endTransmission(); // end call to slave
                }
            }
        }
        timeNow = millis(); // mark current time (in mS)
    }
}