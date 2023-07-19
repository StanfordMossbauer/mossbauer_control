#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 17:07:08 2023

@author: mossbauer_lab
"""
#MANUAL
#http://www.hit.bme.hu/~papay/edu/Lab/33120A_Manual.pdf

import pyvisa
import sys
import atexit

class HP33120A:
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
        self.device.write("VOLT {:f}".format(value))
        return
    
    @property
    def offset(self):
        return self.device.query("VOLT:OFFS?")[:-1]
            
    @offset.setter
    def offset(self, value):
        self.device.write("VOLT:OFFS {:f}".format(value))
        return
    
    
    @property
    def frequency(self):
        return self.device.query("FREQ?")[:-1]
            
    @frequency.setter
    def frequency(self, value):
        # value can be "ON" or "OFF"
        self.device.write("FREQ {}".format(value))
        return

    
    @property
    def burststate(self):
        return self.device.query("BM:STATE?")[:-1]

    @burststate.setter
    def burststate(self, value):
        #value = 1  -> on  value = 0  -> off
        self.device.write("BM:STATE {:d}".format(value))
        return


    @property
    def burstmode(self):
        return self.device.query("BURST:MODE?")[:-1]

    @burstmode.setter
    #BURSt:MODE {TRIGgered|GATed}
    def burstmode(self, value):
        self.device.write("BURST:MODE {}".format(value))
        return

    
    @property
    def burstcycles(self):
        return self.device.query("BM:NCYCLES?")[:-1]

    @burstcycles.setter
    def burstcycles(self, value):
        self.device.write("BM:NCYCLES {:d}".format(value))
        return


    @property
    def burstphase(self):
        return self.device.query("BM:PHASE?")[:-1]

    @burstphase.setter
    def burstphase(self, value):
        self.device.write("BM:PHASE {:d}".format(value))
        return


    @property
    def triggersource(self):
        return self.device.query("TRIGger:SOURce?")[:-1]

    @triggersource.setter
    #{IMMediate|EXTernal|BUS}
    def triggersource(self, value):
        self.device.write("TRIGger:SOURce {}".format(value))
        return

    @property
    def dutycycle(self):
        return self.device.query("PULSe:DCYCle?")[:-1]

    @dutycycle.setter
    #20to80
    def dutycycle(self, value):
        self.device.write("PULSe:DCYCle {}".format(value))
        return


    @property
    def triggerslope(self):
        return self.device.query("TRIGger:SLOPe?")[:-1]

    @triggerslope.setter
    #{POSitive|NEGative}
    def triggerslope(self, value):
        self.device.write("TRIGger:SLOPe {}".format(value))
        return


    def trigger(self):
        self.device.write('*TRG')
        return


     
    def close(self):
        self.device.output = "OFF"
        self.device.close()
        return

    

if __name__ == "__main__":
    siggen = Agilent("GPIB::15::INSTR")
    siggen.frequency = 1000
    siggen.__del__()
    
    

    
    
    