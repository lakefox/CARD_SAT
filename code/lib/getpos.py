from machine import ADC
import time

class POS:
    def __init__(self,baselines) -> None:
        self.baselines = baselines
        self.minsSet = False
        self.minV1 = 0
        self.minV2 = 0
        self.maxV1 = 0
        self.maxV2 = 0
        self.orbitCompleteTime = 7680000;

    def get(self):
        
        # updateVREF();
        vrefs = []
        vrefs.append(ADC(28).read_u16()) # ADC_2
        vrefs.append(ADC(27).read_u16()) # ADC_1
        vrefs.append(ADC(26).read_u16()) # ADC_0

        current1 = (self.baselines[0] - vrefs[0]) / 0.1;
        current2 = (self.baselines[1] - vrefs[1]) / 0.1;

        volt1 = current1 * vrefs[2];
        volt2 = current2 * vrefs[2];
        # using these two voltage measurements we will calculate the angle to the sun

        # posPercent is the percent between 180 and 0
        # volt1 in the front pannel volt2 is the back
        if self.minsSet:
            if (volt1 > volt2):
                posPercent = (volt1 - self.minV1) / (self.maxV1 - self.minV1);
                pos = 180 * posPercent;
            else:
                posPercent = (volt2 - self.minV2) / (self.maxV2 - self.minV2);
                pos = (180 * posPercent) * -1;

            # Send pos immediately
            # Estimated degrees to the sun

            # Add 180 to bring pos to a 360 then get percent
            posPercent = (pos + 180) / 360;

            # percent of orbit complete in time from peak light
            timePercent = (time.ticks_ms() / self.orbitCompleteTime) * 100;

            # Get the average of the estimated percents
            avgPercent = (posPercent + timePercent) / 2;

            avgDeg = 360 * avgPercent;
            # POSUPDATE+degs
            return avgDeg
        else:
            if (time.ticks_ms() <= self.orbitCompleteTime):
                testV1 = ADC(26).read_u16();
                testV2 = ADC(27).read_u16();

                # set maxV* to the max voltage we see
                if (testV1 > self.maxV1):
                    self.maxV1 = testV1
                if (testV2 > self.maxV2):
                    self.maxV2 = testV2
                # set maxV* to the min voltage we see
                if (testV1 < self.minV1):
                    self.minV1 = testV1
                if (testV2 < self.minV2):
                    self.minV2 = testV2
            else:
                self.minsSet = True
            return False
