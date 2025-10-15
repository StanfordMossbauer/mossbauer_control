import pyvisa
import time
import matplotlib.pyplot as plt 
import numpy as np
import csv 
import os
from pyvisa.constants import ControlFlow, Parity, StopBits
import pandas as pd

#https://www.thinksrs.com/products/dc205.html

class dc205:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource("ASRL3::INSTR", )


    def connect(self):
        rm = pyvisa.ResourceManager()
        self.instrument = rm.open_resource("ASRL3::INSTR", )

    def close(self):
        self.instrument.close()

    def write(self, string):
        self.instrument.write(string)
    
    def read(self):
        r = self.instrument.write(":READ?")
        return r

    def query(self, string):
        r = self.instrument.query(string)
        return r

    def set_voltage(self, V):
        self.write(f"VOLT {V}") #can be pos or neg

    
    def output_on(self):
        self.write("SOUT ON")

    def experiment_setup(self, V=2):
        self.write("SOUT ON")
        self.set_voltage(V)


if __name__=='__main__':

    dc205 = dc205()
    dc205.output_on()

    i=1
    while True:
        dc205.set_voltage(2)
        time.sleep(5)
        dc205.set_voltage(-2)
        time.sleep(5)
        i+=1

    dc205.close()

   
    