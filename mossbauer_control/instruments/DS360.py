import pyvisa
import time
import matplotlib.pyplot as plt 
import numpy as np
import csv 
import os
from pyvisa.constants import ControlFlow, Parity, StopBits
import pandas as pd

class DS360:
    def __init__(self, gpib_address=8):
        self.gpib_address = gpib_address
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(f"GPIB::{gpib_address}", )

    def connect(self):
        rm = pyvisa.ResourceManager()
        self.instrument = rm.open_resource(self.address)

    def close(self):
        self.instrument.close()

    def set_sine(self):
        self.instrument.write("FUNC 0") # 0 is for sine, 1 for square, ..

    def set_frequency(self, f):
        self.instrument.write(f"FREQ {f}")
    
    def set_amplitude(self, A): #set amp in V
        self.instrument.write(f"AMPL {A} VP")

    def set_offset(self, D):
        self.instrument.write(f"OFFS {D}")

    def output_on(self):
        self.instrument.write("OUTE 1")

    def output_off(self):
        self.instrument.write("OUTE 0")

if __name__=='__main__':

    drive = DS360(gpib_address = 7)
    drive.set_sine()
    drive.set_frequency(1)
    #drive.set_amplitude(8)
    drive.set_amplitude(4)
    drive.set_offset(0)
    #drive.set_offset(4)
    drive.output_on()

    #the amplitude settings dont work, look at jupyter