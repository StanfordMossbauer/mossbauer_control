# -*- coding: utf-8 -*-
"""
Created on Mon Mar 13 17:00:43 2023

@author: LabLaptop
"""

import pyvisa
import numpy as np
import time as time

class TDS754A:
    def __init__(self, resource):
        self.instrument = pyvisa.ResourceManager().open_resource(resource)

    def read_identity(self):
        identity = self.instrument.query("*IDN?")
        return(identity)
    
    def freq_measurement_setup(self):
        self.instrument.write("MEASU:IMM:TYP FREQ \n")
        return
    
    def freq_measurement(self):
        meas = self.instrument.query("MEASU:IMM:VAL?")
        return meas
        
    def reset(self):
        self.instrument.query("*RST")
        return
        
    def __del__(self):
        self.instrument.close()
        return

if __name__ == "__main__":

    oscilloscope_resource = 'GPIB0::13::INSTR'
    TDS = TDS754A(oscilloscope_resource) # TDS is Techtronix Digital Scope
    
    print(TDS.read_identity())
    TDS.freq_measurement_setup()
    initial_time = time.time()
    time_passage = 0.0
    while time_passage < 1.0:
        print(TDS.freq_measurement())
        print(time_passage)
        time_passage = time.time()-initial_time
    