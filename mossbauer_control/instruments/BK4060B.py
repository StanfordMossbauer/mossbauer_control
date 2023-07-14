#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 17:07:08 2023

@author: mossbauer_lab
#https://bkpmedia.s3.amazonaws.com/downloads/programming_manuals/en-us/4060B_Series_programming_manual.pdf
"""

import pyvisa
import usbtmc
import sys
import atexit
   

class BK4060B:
    '''
    Initiates an instance of the DFR1507A driving a KR26.
    '''
    def __init__(self, resource =  'USB0::62700::60984::575A23113::INSTR' ):
        
        #rm = pyvisa.ResourceManager()
        #self.device = rm.open_resource(resource)
        self.device = usbtmc.Instrument(resource)
        #atexit.register(self.close)  # close self if python process dies
        #print(self.device.query('*IDN?'))
        print(self.device.ask('*IDN?'))

        
        self.deviceSettings = {'mode': [0, 0], 'frequency': [1, 1], 'period': [1, 1], 'width': [0.1, 0.1],
                               'amplitude': [.85, 0.85], 'offset': [0.0, 0.0], 'units': [0, 0],
                               'load': [50, 50],  'polarity' : ['NOR','NOR'] ,'duty': [50, 50], 
                               'burststate': ['OFF', 'OFF'], 'burstmode' :['NCYC','NCYC'],'burstcycles': [1, 1],
                               'output': ['OFF', 'OFF'], 'triggersource': [0, 0],
                               'burstphase': [1, 1], 'triggerdelay': [1, 1], 'active': 1}

    
    @property
    def active(self):
        return self.deviceSettings['active']

    @active.setter
    def active(self, channel):
        self.deviceSettings['active'] = channel
        
        return

    @property
    def mode(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['mode'][channel-1]
            
    @mode.setter
    def mode(self, value):
        #POSSIBLE VALUES:  {SINE | SQUARE | RAMP | PULSE | NOISE | ARB | DC}
        channel = self.deviceSettings['active']
        self.device.write("C{}:BaSic_WaVe WVTP,{}".format(channel,value))
        self.deviceSettings['mode'][channel-1] = value

        check = self.device.ask("*OPC?")
        return check

    
    @property
    def amplitude(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['amplitude'][channel-1]
            
    @amplitude.setter
    def amplitude(self, value):
        channel = self.deviceSettings['active']
        self.device.write("C{}:BaSic_WaVe AMP,{}".format(channel, value))
        self.deviceSettings['amplitude'][channel-1] = value
        check = self.device.ask("*OPC?")
        return check

    
    @property
    def offset(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['offset'][channel-1]
            
    @offset.setter
    def offset(self, value):
        channel = self.deviceSettings['active']
        self.device.write("C{}:BaSic_WaVe OFST,{}".format(channel, value))
        self.deviceSettings['offset'][channel-1] = value
        check = self.device.ask("*OPC?")
        return check


    @property
    def frequency(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['frequency'][channel-1]
            
    @frequency.setter
    def frequency(self, value):
        channel = self.deviceSettings['active']
        self.device.write("C{}:BaSic_WaVe FRQ,{}".format(channel, value))
        self.deviceSettings['frequency'][channel-1] = value
        check = self.device.ask("*OPC?")
        return check

    
    @property
    def output(self):
        channel = self.deviceSettings['active']
        #print(channel,self.deviceSettings['output'])
        return self.deviceSettings['output'][channel-1] 
            
    @output.setter
    def output(self, value):
        # value can be "ON" or "OFF"
        channel = self.deviceSettings['active']
        
        self.deviceSettings['output'][channel-1] = value

        output = self.deviceSettings['output'][channel-1]
        load = self.deviceSettings['load'][channel-1]
        polarity = self.deviceSettings['polarity'][channel-1]
        self.device.write("C{}:OUTP {},LOAD,{},PLRT,{}".format(channel, output, load, polarity))
        
        check = self.device.ask("*OPC?")
        return check

    
    @property
    def load(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['load'][channel-1]
            
    @load.setter
    def load(self, value):
        channel = self.deviceSettings['active']
        self.deviceSettings['load'][channel-1] = value

        output = self.deviceSettings['output'][channel-1]
        load = elf.deviceSettings['load'][channel-1]
        polarity = self.deviceSettings['polarity'][channel-1]
        self.device.write("C{}:OUTP {},LOAD,{},PLRT,{}".format(channel, output, load, polarity))
        
        check = self.device.ask("*OPC?")
        return check


    @property
    def polarity(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['polarity'][channel-1] 
            
    @polarity.setter
    def polarity(self, value):
        channel = self.deviceSettings['active']

        self.deviceSettings['polarity'][channel-1] = value

        output = self.deviceSettings['output'][channel-1]
        load = self.deviceSettings['load'][channel-1]
        polarity = self.deviceSettings['polarity'][channel-1]
        self.device.write("C{}:OUTP {},LOAD,{},PLRT,{}".format(channel, output, load, polarity))
        
        check = self.device.ask("*OPC?")
        return check


    
    @property
    def burststate(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['burststate'][channel-1]

    @burststate.setter
    def burststate(self, value):
        channel = self.deviceSettings['active']
        #"ON or OFF""
        #print("C{}:BTWV STATE,{}".format(channel , value))
        self.device.write("C{}:BTWV STATE,{}".format(channel , value))
        self.deviceSettings['burststate'][channel-1] = value
        check = self.device.ask("*OPC?")
        return check




    @property
    def burstmode(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['burstmode'][channel-1]

    @burstmode.setter
    def burstmode(self, value):
        #{NCYC|GATE}
        channel = self.deviceSettings['active']
        self.device.write("C{}:BTWV GATE_NCYC,{}".format(channel,value))
        self.deviceSettings['burstmode'][channel-1] = value
        check = self.device.ask("*OPC?")
        return check


    
    @property
    def burstcycles(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['burstcycles'][channel-1]

    @burstcycles.setter
    def burstcycles(self, value):
        channel = self.deviceSettings['active']
        self.device.write("C{}:BTWV TIME,{}".format(channel, value))
        self.deviceSettings['burstcycles'][channel-1] = value
        check = self.device.ask("*OPC?")
        return check


    @property
    def burstphase(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['burstphase'][channel-1]

    @burstphase.setter
    def burstphase(self, value):
        channel = self.deviceSettings['active']
        self.device.write("C{}:BTWV STPS,{}".format(channel, value))
        self.deviceSettings['burstphase'][channel-1] = value
        check = self.device.ask("*OPC?")
        return check


    @property
    def triggersource(self):
        channel = self.deviceSettings['active']
        return self.deviceSettings['triggersource'][channel-1]

    @triggersource.setter
    #{INT|EXT|MAN}
    def triggersource(self, value):
        channel = self.deviceSettings['active']
        self.device.write("C{}:BTWV TRSR,{}".format(channel,value))
        self.deviceSettings['triggersource'][channel-1] = value
        check = self.device.ask("*OPC?")
        return check


    #@property
    #def triggerslope(self):
    #    return self.device.query("TRIGger:SLOPe?")[:-1]

    #@triggerslope.setter
    ##{POSitive|NEGative}
    #def triggerslope(self, value):
    #    self.device.write("TRIGger:SLOPe {}".format(value))
    #    return

    
    #def trigger(self):
    #    self.device.write('*TRG')
    #    return

    def close(self):
        self.active = 1
        self.device.output = "OFF"
        self.active = 2
        self.device.output = "OFF"
        self.device.close()
        return
        

if __name__ == "__main__":
    siggen = BK4060B('USB0::62700::60984::575A23113::0::INSTR')
    siggen.frequency = 1000
    siggen.__del__()
    
    

    