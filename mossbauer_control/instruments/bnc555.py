import pyvisa
import time
import matplotlib.pyplot as plt 
import numpy as np
import csv 
import os
from pyvisa.constants import ControlFlow, Parity, StopBits
import pandas as pd


class bnc555:
    def __init__(self, gpib_address=1):
        self.gpib_address = gpib_address
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(f"GPIB::{gpib_address}", )


    def connect(self):
        rm = pyvisa.ResourceManager()
        self.instrument = rm.open_resource(self.address)

    def close(self):
        self.instrument.close()

    def write(self, string):
        self.instrument.write(string)

    def query(self, string):
        r = self.instrument.query(string)
        return r

    def reset(self):
        self.write("*RST")


    def setup(self): #get the bnc box in the correct state
        self.instrument.write_termination = '\r\n'
        self.instrument.read_termination = '\r\n'
        self.instrument.timeout = 5000

    def set_clock_mode(self, mode='BURST'): #usually burst mode
        self.instrument.write(f":PULSE0:MODE {mode}")

    def set_clock_f(self, period=0.00032):
        #somehow this is in units of 10 seconds. will figure it out in the future.
        self.instrument.write(f":PULSE0:PER {period}")

    def set_ext_trigger(self):
        self.instrument.write(":PULSE0:EXT:MODE TRIG")
        self.instrument.write(":PULSE0:EXT:EDGE RIS")
        self.instrument.write(":PULSE0:EXT:LEV 1.0")

    def enable(self, channel, status = 'ON'):
        self.instrument.write(f":PULSE{channel}:STAT {status}") #status = on,off
    
    def burst_count(self, channel, count):
        self.instrument.write(f":PULSE{channel}:BCO {count}")
    
    def pulse_width(self, channel, width):
       self.instrument.write(f":PULSE{channel}:WIDT {width}")

    def pulse_delay(self, channel, delay):
        self.instrument.write(f":PULSE{channel}:DEL {delay}")

    def channel_mode(self, channel, mode='BURST'):
        self.instrument.write(f":PULSE{channel}:CMOD {mode}")

    def experiment_setup(self, f=30, nbursts=5):
        #note there is an extra division by 10 because this is the weird unit of set_clock_f
        pulse_period =  int((1/(f*nbursts*2*10)-1e-7)*1e6)/1e6
        self.setup()   
        self.reset()

        #configure sys clock for 300Hz from 60Hz trigger
        self.set_clock_mode('BURST')
        self.set_ext_trigger()
        self.enable(0, 'ON')
        self.set_clock_f(pulse_period)
        self.burst_count(0, nbursts)

        #set channel 1 for camera trigger
        self.enable(1, 'ON')
        self.channel_mode(1, 'BURST')
        self.burst_count(1, nbursts)
        self.pulse_width(1, 0.0001)
        self.pulse_delay(1, 0)



if __name__=='__main__':
    bnc = bnc555(gpib_address = 1)

    bnc.setup()
    bnc.reset()

    #configure sys clock for 300Hz from 60Hz trigger
    bnc.set_clock_mode('BURST')
    bnc.set_ext_trigger()
    bnc.enable(0, 'ON')
    bnc.set_clock_f(0.00032)
    bnc.burst_count(0, 5)

    #set channel 1 for camera trigger
    bnc.enable(1, 'ON')
    bnc.channel_mode(1, 'BURST')
    bnc.burst_count(1, 5)
    bnc.pulse_width(1, 0.0001)
    bnc.pulse_delay(1, 0)

    #set channel 2 for camera DAQ
    bnc.enable(2, 'ON')
    bnc.channel_mode(2, 'BURST')
    bnc.burst_count(2, 4)
    bnc.pulse_width(2, 0.0001)
    bnc.pulse_delay(2, 0.031)



