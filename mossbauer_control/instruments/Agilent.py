#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 17:07:08 2023

@author: mossbauer_lab
"""

import pyvisa
import sys
import atexit

class Agilent:
    '''
    Initiates an instance of the DFR1507A driving a KR26.
    '''
    def __init__(self, resource):
        
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource(resource)
        atexit.register(self.close)  # close self if python process dies
        print(self.device.query('*IDN?'))
        
    @property
    def mode(self):
        return self.device.query("FUNC?")[:-1]
            
    @mode.setter
    def mode(self, value):
        #POSSIBLE VALUES: SQU, SIN, 
        self.device.write("FUNC {}".format(value))
        #can add others 
        return
    
    @property
    def amplitude(self):
        return self.device.query("VOLT?")[:-1]
            
    @amplitude.setter
    def amplitude(self, value):
        self.device.write("VOLT {:f}")
        return
    
    @property
    def offset(self):
        return self.device.query("VOLT:OFFS?")[:-1]
            
    @offset.setter
    def offset(self, value):
        self.device.write("VOLT:OFFS? {:f}")
        return
    
    @property
    def output(self):
        return self.device.query("OUTPUT?")[:-1]
            
    @output.setter
    def output(self, value):
        # value can be "ON" or "OFF"
        self.device.write("OUTPUT {}".format(value))
        return
    
    @property
    def frequency(self):
        return self.device.query("FREQ?")[:-1]
            
    @frequency.setter
    def frequency(self, value):
        # value can be "ON" or "OFF"
        self.device.write("FREQ {}".format(value))
        return
    
    def close(self):
        self.device.output = "OFF"
        self.device.close()
    

if __name__ == "__main__":
    siggen = Agilent("GPIB::14::INSTR")
    siggen.frequency = 1000
    siggen.__del__()
    
    

    
    
    
