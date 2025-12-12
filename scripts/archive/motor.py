import pyvisa
import sys, os
import numpy as np

from mossbauer_control.instruments import Agilent, DFR1507A
from mossbauer_control.utils import *


class Motor:
    '''
    Note this is unused these days, since it controls the stepper motor.
    Still, for now leaving it here because its higher-level than the instruments
    it uses.
    
    '''
    def __init__(self, agilent = "GPIB0::14::INSTR",arduino = "/dev/ttyACM1" ):
        
        self.motordrive = DFR1507A(arduino)

        self.motordrive.AWoff()
        self.motordrive.setResolution(1)
        self.motordrive.setDirection("CW")
        

        self.siggen = Agilent(agilent)

        self.siggen.mode = "SQU"
        self.siggen.amplitude = 5
        self.siggen.offset = -2.5
        self.siggen.output = "ON"

        self.motorSettings = {'velocity': 0, 'resolution': 1}

    def updateSettings(self):

        self.motordrive.setResolution = self.resolution

        if self.resolution == 1:
            RES = 2*0.00288/360 # (ball screw lead mm/rev) * (?) / 1rev
        else:
            RES = 2*0.009/360 # (ball screw lead mm/rev) * (?) / 1rev

        if self.velocity>=0:
            self.motordrive.setDirection('CCW')
        else:
            self.motordrive.setDirection('CW')

        self.siggen.frequency = np.abs(self.velocity/RES)
        #print(self.velocity, RES)


    def log_output(self, logfile):
        logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s:%(levelname)s:\t%(message)s',
                handlers=[
                    logging.FileHandler(logfile),
                    logging.StreamHandler()
                ],
                )
        log = logging.getLogger('scanlog')
        sys.stdout = StreamToLogger(log, logging.INFO)
        sys.stderr = StreamToLogger(log, logging.ERROR)
        return

        
    @property
    def velocity(self):
        return self.motorSettings['velocity']

            
    @velocity.setter
    def velocity(self, value):
        self.motorSettings['velocity'] = value
        self.updateSettings()
        return
    
    @property
    def resolution(self):
        return self.motorSettings['resolution']
            
    @resolution.setter
    def resolution(self, value): 
        self.motorSettings['resolution'] = value
        self.updateSettings()
        return
    
    def start(self):
        self.motordrive.AWon()
        return

    def stop(self):
        self.motordrive.AWoff()
        return

    @property
    def flagA(self):
        return self.motordrive.readFlagState()[0]

    @property
    def flagB(self):
        return self.motordrive.readFlagState()[1]
    
    def close(self):
        self.siggen.close()
        self.motordrive.close()
    
    def __del__(self):

        self.siggen.output = "OFF"
        self.motordrive.AWoff()
        self.motordrive.__del__()
        self.siggen.__del__()


if __name__=='__main__':
    print('starting')
    scan = ScanController()
    # Turn on the base high voltage
    scan.moku.setBaseHV(1, 1) # Default to 1kV bias on channel 1
