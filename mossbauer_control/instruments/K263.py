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

    def reset(self):
        self.instrument.write("*RST")

    def set_current_mode(self):
        self.instrument.write(":SOUR:FUNC CURR")

    def set_current_range(self, range):
        self.instrument.write(f":SOUR:CURR:RANG,{range}")
    
    def set_current(self, current):
        self.instrument.write(f":SOUR:CURR,{current}")

    def turn_on(self):
        self.instrument.write(":OUTP ON")


if __name__ == "__main__":
    
    calibrator = K263(gpib_address = 8)
    calibrator.reset()
    calibrator.set_current_mode()
    calibrator.set_current_range(10e-9)
    calibrator.set_current(5e-9)
    calibrator.turn_on()

    i=0
    while i<10:
        calibrator.set_current(5e-9)
        time.sleep(1000)
        calibrator.set_current(-5e-9)
        time.sleep(1000)
        i+=1

