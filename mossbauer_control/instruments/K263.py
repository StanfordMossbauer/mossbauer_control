# Keithley 263 Programming Manual: https://download.tek.com/manual/263_901_01E.pdf
import pyvisa
import matplotlib.pyplot as plt
import numpy as np
import time
import pandas as pd


class K263:
    def __init__(self, gpib_address=8):
        self.gpib_address = gpib_address
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(f"GPIB::{gpib_address}", )


    def set_current_mode(self):
        self.instrument.write("F1X")

    def set_current_range(self):
        self.instrument.write("R5X") #FOR 20nA
    
    def set_current(self, current):
        self.instrument.write(f"V{current}X") #current is in amps format: 1.0E-09

    def operate(self):
        self.instrument.write("O1X")

    def stop(self):
        self.instrument.write("O0X")

    def experiment_setup(self):
        self.set_current_mode()
        self.set_current_range()
        self.set_current(1E-10)
        self.operate()


if __name__ == "__main__":
    
    calibrator = K263(gpib_address = 9)
    calibrator.set_current_mode()
    calibrator.set_current_range()
    calibrator.set_current(10E-9)
    calibrator.operate()

    i=0
    while True:
        calibrator.set_current(-1E-9)
        time.sleep(1000)
        calibrator.set_current(1E-9)
        time.sleep(1000)
        i+=1

    calibrator.stop()





