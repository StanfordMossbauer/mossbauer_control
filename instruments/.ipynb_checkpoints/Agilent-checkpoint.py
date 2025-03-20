#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 17:07:08 2023

@author: mossbauer_lab
"""

import pyvisa
import sys
import atexit

#from mossbauer_control.instruments import MossbauerInstrument
from .base import MossbauerInstrument
   

class Agilent(MossbauerInstrument):
    '''
    Initiates an instance of the DFR1507A driving a KR26.
    '''
    def __init__(self, resource):
        
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource(resource)
        atexit.register(self.close)  # close self if python process dies
        print(self.device.query('*IDN?'))

    def setup_mossbauer_scan(self):
        self.mode = 'PULSE'
        self.frequency = 1000
        self.amplitude = 5
        self.offset = 2.5 # somehow the hp signal generator outputs a value that isd different from seeting. 1.3 gives 2.5
        self.triggersource = 'BUS'
        self.output = 'ON'
        return
        
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

    
    @property
    def burststate(self):
        return self.device.query("BURST:STATE?")[:-1]

    @burststate.setter
    def burststate(self, value):
        #value = 1  -> on  value = 0  -> off
        self.device.write("BURST:STATE {:d}".format(value))
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
        return self.device.query("BURST:NCYCLES?")[:-1]

    @burstcycles.setter
    def burstcycles(self, value):
        self.device.write("BURST:NCYCLES {:d}".format(value))
        return

    @property
    def burstphase(self):
        return self.device.query("BURST:PHASE?")[:-1]

    @burstphase.setter
    def burstphase(self, value):
        self.device.write("BURST:PHASE {:d}".format(value))
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
    def triggerslope(self):
        return self.device.query("TRIGger:SLOPe?")[:-1]

    @triggerslope.setter
    #{POSitive|NEGative}
    def triggerslope(self, value):
        self.device.write("TRIGger:SLOPe {}".format(value))
        return

    @property
    def dutycycle(self):
        return self.device.query("TRIGger:SLOPe?")[:-1]

    @dutycycle.setter
    #{POSitive|NEGative}
    def dutycycle(self, value):
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
    siggen = Agilent("GPIB::14::INSTR")
    siggen.frequency = 1000
    siggen.__del__()
    
    

    
    
