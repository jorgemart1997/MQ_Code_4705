import time
import math
from MCP3008 import MCP3008

class MQ():

    ######################### Hardware Related Macros #########################
    MQ_PIN                       = 0      # define which analog input channel you are going to use (MCP3008)
    RL_VALUE                     = 10     # RL is 10 kilo ohms, according to data sheet.
    RO_CLEAN_AIR_FACTOR          = 60     # RO_CLEAR_AIR_FACTOR=(Sensor resistance in clean air)/RO,
                                          # which is derived from the chart in datasheet

    ######################### Software Related Macros #########################
    CALIBRATION_SAMPLE_TIMES     = 50       # define how many samples you are going to take in the calibration phase
    CALIBRATION_SAMPLE_INTERVAL  = 500      # define the time interal(in milisecond) between each samples in the
                                            # cablibration phase
    READ_SAMPLE_INTERVAL         = 50       # define how many samples you are going to take in normal operation
    READ_SAMPLE_TIMES            = 5        # define the time interal(in milisecond) between each samples in
                                            # normal operation

    ######################### Application Related Macros ######################
      GAS_ALC                      = 0      # Gas_ALC macro declaration.

    def __init__(self, Ro=10, analogPin=0):  # come back to this
        self.Ro = Ro
        self.MQ_PIN = analogPin
        self.adc = MCP3008()

        self.ALCCurve = [-0.92,0.34,-0.59]                                        # First point of graph (0.1, 2.4)
                                                                                  # Point [log(.1),Log(2.4)], and then the slope which was calculated to be -0.59

        print("Calibrating...")
        self.Ro = self.MQCalibration(self.MQ_PIN)                                 # This will set self.Ro equal to val, which will hold Ro.
        print("Calibration is done...\n")
        print("Ro=%f kohm" % self.Ro)


    def MQPercentage(self):
        val = {}
        read = self.MQRead(self.MQ_PIN)                                          # read will be set to Rs.
        val["GAS_ALC"]  = self.MQGetGasPercentage(read/self.Ro, self.GAS_ALC)    # val["GAS_ALC"] will be set to Rs/Ro.
        return val                                                               # This val will hold the final value that will be displayed on the monitor.

    ######################### MQResistanceCalculation #########################
    # Input:   raw_adc - raw value read from adc, which represents the voltage
    # Output:  the calculated sensor resistance
    # Remarks: The sensor and the load resistor forms a voltage divider. Given the voltage
    #          across the load resistor and its resistance, the resistance of the sensor
    #          could be derived.
    ############################################################################
    def MQResistanceCalculation(self, raw_adc):
        return float(self.RL_VALUE*(1023.0-raw_adc)/float(raw_adc));


    ######################### MQCalibration ####################################
    # Input:   mq_pin - analog channel
    # Output:  Ro of the sensor
    # Purpose: This function assumes that the sensor is in clean air. It use
    #          MQResistanceCalculation to calculates the sensor resistance in clean air
    #          and then divides it with RO_CLEAN_AIR_FACTOR.
    # ROCAF = RS/RO ---> R0*ROCAF = RS ---> Ro = RS/RO_CLEAN_AIR_FACTOR
    # val = Ro;
    ############################################################################
    def MQCalibration(self, mq_pin):
        val = 0.0
        for i in range(self.CALIBRATION_SAMPLE_TIMES):          # take multiple samples
            val += self.MQResistanceCalculation(self.adc.read(mq_pin))
            time.sleep(self.CALIBRATION_SAMPLE_INTERVAL/1000.0)

        val = val/self.CALIBRATION_SAMPLE_TIMES                 # calculate the average value
                                                                # Going to hold the value of the sensor resistance, Rs.
        val = val/self.RO_CLEAN_AIR_FACTOR                      # divided by RO_CLEAN_AIR_FACTOR yields the Ro
                                                                # according to the chart in the datasheet
                                                                # this val will be val = Rs/Ro_clean_air_factor.

        return val;                                             # Returns Ro.


    #########################  MQRead ##########################################
    # Input:   mq_pin - analog channel
    # Output:  Rs of the sensor
    # Purpose: This function use MQResistanceCalculation to caculate the sensor resistenc (Rs).
    #          The Rs changes as the sensor is in the different concentration of alcohol.
    #          The sample times and the time interval between samples could be configured
    #          by changing the definition of the macros.
    ############################################################################
    def MQRead(self, mq_pin):
        rs = 0.0

        for i in range(self.READ_SAMPLE_TIMES):
            rs += self.MQResistanceCalculation(self.adc.read(mq_pin))
            time.sleep(self.READ_SAMPLE_INTERVAL/1000.0)

        rs = rs/self.READ_SAMPLE_TIMES

        return rs           # Returns Rs.

    #########################  MQGetGasPercentage ##############################
    # Input:   rs_ro_ratio - Rs divided by Ro
    #          gas_id      - target gas type
    # Output:  ppm of the target gas
    # Purpose: This function passes different curves to the MQGetPercentage function which
    #          calculates the mg/L of the alcohol curve.
    ############################################################################
    def MQGetGasPercentage(self, rs_ro_ratio, gas_id):              # rs_ro_ratio is read/self.Ro which is equal to Rs/Ro.
        if ( gas_id == self.GAS_ALC ):
          return self.MQGetPercentage(rs_ro_ratio, self.ALCCurve)
        else
            return 0


    #########################  MQGetPercentage #################################
    # Input:   rs_ro_ratio - Rs divided by Ro
    #          pcurve      - pointer to the curve of the target gas
    # Output:  The X value in mg/L of the alcohol (of the target gas).
    # Remarks: By using the slope and a point of the line. The x(logarithmic value of ppm)
    #          of the line could be derived if y(rs_ro_ratio) is provided. As it is a
    #          logarithmic coordinate, power of 10 is used to convert the result to non-logarithmic
    #          value.
    ############################################################################
    # Gets the parameters self, the rs_ro ratio which is the same always, and pcurve which will
    # always point to AlCCurve.
    def MQGetPercentage(self, rs_ro_ratio, pcurve):
        return (math.pow(10,( ((math.log(rs_ro_ratio)-pcurve[1])/ pcurve[2]) + pcurve[0])))
