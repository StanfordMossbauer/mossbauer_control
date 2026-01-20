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
    
    def set_Vpp(self, A): #set amp in V
        self.instrument.write(f"AMPL {A} VP")

    def set_offset(self, D):
        self.instrument.write(f"OFFS {D}")

    def output_on(self):
        self.instrument.write("OUTE 1")

    def output_off(self):
        self.instrument.write("OUTE 0")

    def experiment_setup(self,f=30,A=6.579):
        self.set_sine()
        self.set_frequency(f)
        self.set_Vpp(A)
        self.set_offset(0)
        self.output_on()

if __name__=='__main__':

    drive = DS360(gpib_address = 8)
    amp = 6.579
    offset_V = amp/2
    drive.set_sine()
    drive.set_frequency(30)
    drive.set_amplitude(amp)
    drive.set_offset(offset_V)
    drive.output_on()

    #the amplitude settings dont work, look at jupyter