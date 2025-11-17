#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 24 12:00:41 2025

@author: chiarabrandenstein
"""

import pyvisa
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import csv
import os

TIME_CONSTANTS = {
    0: 10e-6, 1: 30e-6, 2: 100e-6, 3: 300e-6, 4: 1e-3, 5: 3e-3, 6: 10e-3,
    7: 30e-3, 8: 100e-3, 9: 300e-3, 10: 1, 11: 3, 12: 10, 13: 30, 14: 100,
    15: 300, 16: 1e3, 17: 3e3, 18: 10e3, 19: 30e3
}

SENSITIVITIES = {
    0: 2e-9, 1: 5e-9, 2: 10e-9, 3: 20e-9, 4: 50e-9, 5: 100e-9, 6: 200e-9,
    7: 500e-9, 8: 1e-6, 9: 2e-6, 10: 5e-6, 11: 10e-6, 12: 20e-6, 13: 50e-6,
    14: 100e-6, 15: 200e-6, 16: 500e-6, 17: 1e-3, 18: 2e-3, 19: 5e-3,
    20: 10e-3, 21: 20e-3, 22: 50e-3, 23: 100e-3, 24: 200e-3, 25: 500e-3, 26: 1
}

# SENSITIVITIES_SR830 = SENSITIVITIES_SR810 | {
#     27: 2, 28: 5, 29: 10, 30: 20, 31: 50
# }


class SRS810:
    def __init__(self, gpib_address=11):
        self.gpib_address = gpib_address
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(f"GPIB::{gpib_address}")
        self.instrument.baud_rate = 9600
        self.instrument.write("SEND 0")  # one-shot mode

    def set_sensitivity(self, sensitivity):
        closest_sensitivity = min(SENSITIVITIES.values(), key=lambda x: abs(x - sensitivity))
        sensitivity = list(SENSITIVITIES.keys())[list(SENSITIVITIES.values()).index(closest_sensitivity)]
        self.instrument.write(f"SENS {sensitivity}")
        return SENSITIVITIES[sensitivity]

    def get_sensitivity(self):
        return float(self.instrument.query(f"SENS ?"))

    def set_time_constant(self, time_constant):
        closest_time_constant = min(TIME_CONSTANTS.values(), key=lambda x: abs(x - time_constant))
        time_constant = list(TIME_CONSTANTS.keys())[list(TIME_CONSTANTS.values()).index(closest_time_constant)]
        self.instrument.write(f"OFLT {time_constant}")
        return TIME_CONSTANTS[time_constant]

    def get_time_constant(self):
        return float(self.instrument.query(f"OFLT ?"))

    def set_output_amplitude(self, amplitude):
        self.instrument.write(f"SLVL {amplitude}")

    def set_output_frequency(self, frequency):
        self.instrument.write(f"FREQ {frequency}")

    def set_ref_source(self, status = 0): #external = 0, internal = 1
        self.instrument.write(f"FMOD {status}")

    def read_all(self):
        res = self.instrument.query("SNAP? 1,2,3")
        X, Y, R = np.array(res.strip().split(",")).astype(float)
        return X, Y, R

    def read_R(self):
        R = self.instrument.query("SNAP? 3")
    
    def read_f_ref(self):
        fref = self.instrument.query("FREQ?")
        return fref
    
    def read_phase(self):
        theta = self.instrument.query("PHAS?")
        return theta

    # def read_R(self): return float(self.instrument.query("OUTP? 3"))
    # def read_theta(self): return float(self.instrument.query("OUTP? 4"))

    def reset(self): 
        self.instrument.write("*RST")
    def close(self):
        self.instrument.close()
        self.rm.close()

    def sens(self, i):
        self.instrument.write(f"SENS {i}")

    def sync_filter(self, i = 0): #i = 0 is off and i =1 is on
        self.instrument.write(f"SYNC {i}")

    def low_pass_filter(self, dB = 0): #can set to 6, 12, 18, 24 dB cannot be turned off I think
        self.instrument.write(f"OFSL {dB}")

    def channel_setup(self, i=1):  #set to A-B for i = 1
        self.instrument.write(f"ISRC {i}")

    def timeconst(self, i):
        self.instrument.write("OFLT {i}") 

    def set_float(self, i=0):
        self.instrument.write("IGND {i}")

    def auto_reserve(self):
        self.instrument.write("ARSV")
    
    def line_filt(self, i = 0): #can be off, 1 or 2
        self.instrument.write("ILIN {i}")

    def reserve(self, state=0): #high, low or normal, default high
        self.instrument.write(f"RMOD {state}")

    def experiment_setup(self, f):
        self.reset()
        self.sens(21) #20mV
        self.set_ref_source(0) #set to external reference
        self.low_pass_filter(0) #low pass to 6dB
        self.channel_setup(1) #channel to A-B
        self.set_float(0) #shield to float
        self.reserve(0) #high reserve
        self.line_filt(0) #line filter off
        self.set_time_constant(9/f)
        time.sleep(10)

    # def clean(value):
    #     if isinstance(value, str):
    #         value = value.strip()
    #     try:
    #         return float(value)
    #     except ValueError:
    #         return value  # fallback if it's not numeric

    def take_data(self):
        #R = self.read_R()
        X, Y, R = self.read_all()
        fref = float(self.read_f_ref().strip())
        phase = float(self.read_phase().strip())
        return float(R),  phase, fref

if __name__ == "__main__":
    # # Run for 40 Hz drive
    # f=30
    # srs = SRS810(gpib_address=11)
    # srs.reset()
    # srs.sens(21) #20mV
    # srs.set_ref_source(0) #set to external reference
    # srs.low_pass_filter(0) #low pass to 6dB
    # srs.channel_setup(1) #channel to A-B
    # srs.set_float(0) #shield to float
    # srs.reserve(0) #high reserve
    # srs.line_filt(0) #line filter off
    # srs.set_time_constant(9/f)
    # # time.sleep(10)


    srs = SRS810(gpib_address=11)
    srs.experiment_setup(f=30)
    data = srs.take_data()

    

    # results = []
    # f = 30  # Hz
    # #time_const = 15 / f
    # #srs.set_time_constant(time_const)

    # csv_path = r'C:\Users\mossbauer\Documents\data\1106\sr810_test.csv'
    # os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    # fieldnames = ["f_ref", "R", "theta", "X", "Y"]
    
    # def clean(value):
    #     if isinstance(value, str):
    #         value = value.strip()
    #     try:
    #         return float(value)
    #     except ValueError:
    #         return value  # fallback if it's not numeric

    # with open(csv_path, mode="a", newline="") as csvfile:
    #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #     if csvfile.tell() == 0:
    #         writer.writeheader()
    #     # Main data acquisition loop
    #     while True:
    #         X, Y, R = srs.read_all()
    #         fref = srs.read_f_ref()
    #         phase = srs.read_phase()

    #         # Write the current data row to the CSV
    #         writer.writerow({
    #             "f_ref": clean(fref),
    #             "R": clean(R),
    #             "theta": clean(phase),
    #             "X": clean(X),
    #             "Y": clean(Y)
    #         })

    #         time.sleep(1)

    # # Extract data for plotting
    # R_vals = [r["R"] for r in results]
    # theta_vals = [r["theta"] for r in results]
    # f_refs = [r["f_ref"] for r in results]

    # plt.figure()
    # plt.title('amp')
    # plt.plot(R_vals, label="R (amplitude)", color = "purple")
    # plt.show()
    
    # plt.figure()
    # plt.title('theta')
    # plt.plot(theta_vals, label="Theta (phase)", color="pink")
    # plt.show()

    # plt.figure()
    # plt.title('fref')
    # plt.plot(f_refs)
    # plt.show()