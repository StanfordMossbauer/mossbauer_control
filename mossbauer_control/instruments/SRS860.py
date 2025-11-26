#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 09:35:21 2025

@author: chiarabrandenstein
"""

# SRS830 Programming Manual: https://thinksrs.com/downloads/pdfs/manuals/SR860m.pdf
import pyvisa
import matplotlib.pyplot as plt
import numpy as np
import time
import pandas as pd

# Time constants are in seconds
TIME_CONSTANTS = {0: 1e-6, 1:3e-6,
    2: 10e-6, 3: 30e-6, 4: 100e-6, 5: 300e-6, 6: 1e-3, 7: 3e-3, 8: 10e-3,
    9: 30e-3, 10: 100e-3, 11: 300e-3, 12: 1, 13: 3, 14: 10, 15: 30, 16: 100,
    17: 300, 18: 1e3, 19: 3e3, 20: 10e3, 21: 30e3
}

# Sensitivities are in volts
SENSITIVITIES = {0: 1e-9,
    1: 2e-9, 2: 5e-9, 3: 10e-9, 4: 20e-9, 5: 50e-9, 6: 100e-9, 7: 200e-9,
    8: 500e-9, 9: 1e-6, 10: 2e-6, 11: 5e-6, 12: 10e-6, 13: 20e-6, 14: 50e-6,
    15: 100e-6, 16: 200e-6, 17: 500e-6, 18: 1e-3, 19: 2e-3, 20: 5e-3,
    21: 10e-3, 22: 20e-3, 23: 50e-3, 24: 100e-3, 25: 200e-3, 26: 500e-3,
    27: 1
}


class SRS860:
    def __init__(self, gpib_address=10):
        self.gpib_address = gpib_address
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(f"GPIB::{gpib_address}", )
        #self.instrument.baud_rate = 9600 not for GPIB instrument
        #self.instrument.write("SEND 0") #shot mode (1 for loop mode) for older instruments only


    def set_sensitivity(self, sensitivity):
        self.instrument.write(f"SCAL {sensitivity}")
    
    def get_sensitivity(self):
        return float(self.instrument.query(f"SENS ?"))
    
    
    def set_time_constant(self, time_constant):
        # closest_time_constant = min(TIME_CONSTANTS.values(), key=lambda x: abs(x - time_constant))
        # time_constant = list(TIME_CONSTANTS.keys())[list(TIME_CONSTANTS.values()).index(closest_time_constant)]
        # self.instrument.write(f"OFLT {time_constant}")
        # return TIME_CONSTANTS[time_constant]
        self.instrument.write(f"OFLT {time_constant}")
    
    def get_time_constant(self):
        return float(self.instrument.query(f"OFLT ?"))

    def set_output_amplitude(self, amplitude):
        self.instrument.write(f"SLVL {amplitude}")

    def set_output_frequency(self, frequency):
        self.instrument.write(f"FREQ {frequency}")


    def set_resolution(self, resolution):
        self.instrument.write(f"DDEF 1,{resolution}")

    def read_X(self):
        return float(self.instrument.query("OUTP? 1"))

    def read_Y(self):
        return float(self.instrument.query("OUTP? 2"))
    
    def read_R(self):
        return float(self.instrument.query("OUTP? 3"))

    def read_theta(self):
        return float(self.instrument.query("OUTP? 4"))
    
    def auto_sensitivity(self):
        self.instrument.write("ARNG")
        
    def ext_reference(self): #can be external, internal, dual or chop
        self.instrument.write("RSRC EXT")
        
    def TTL_trigger_setup(self):
        self.instrument.write('RTRG POSTTL')
        
    def set_impedance(self): #for high impedance
        self.instrument.write('REFZ 1M')
        

    def read_all(self):
        res = self.instrument.query("SNAP? 2,3,16")
        #R, theta, f_ref = np.array(res[:-1].split(",")).astype('float')
        R, theta, f_ref = np.array(res.split(",")).astype('float')
        return R, theta, f_ref 

    def reset(self):
        self.instrument.write('REST')
        
    def set_filter(self, i=2):
        self.instrument.write(f'OFSL {i}')
        
    def sync_setting(self, i=1):
        self.instrument.write(f'SYNC {i}')
        
    def input_range(self, i=2): #for 100mV
        self.instrument.write(f'IRNG {i}')
        
    def voltage_mode(self):
        self.instrument.write('IVMD VOLT')
    
    def differential_measurement(self):
        self.instrument.write('ISRC A-B')
    
    def DC_mode(self):
        self.instrument.write('ICPL DC')
        
    def float_mode(self):
        self.instrument.write('IGND FLO')
        
        
    
        
    
    #clear buffer
    #set reference (internal or extenal)

    def close(self):
        self.instrument.close()
        self.rm.close()
    
    def experiment_setup(self):
        self.reset()
        self.set_sensitivity(12) #added
        self.set_time_constant(11)
        
        self.ext_reference()
        self.TTL_trigger_setup()
        self.set_impedance()
        
        self.set_filter()
        self.sync_setting()
        self.input_range()
        self.voltage_mode()
        self.differential_measurement()
        self.DC_mode()
        self.float_mode()
        
        
        
        
        



if __name__ == "__main__":
    #run for 40Hz drive
    srs = SRS860(gpib_address = 10)
    f=41
    
    srs.experiment_setup(f)
    #srs.reset()
    #srs.set_sensitivity(100) #added
    results = []
    
    #time_const = 9/f
    #srs.set_time_constant(time_const)
    
    i = 0
    while i <10:
        R,theta, f_ref = srs.read_all()

        results.append(dict(
            f_ref = f_ref,
            R = R,
            theta = theta
            ))
        i+=1

    directory = 'C:\\Users\\Mossbauer\\Documents\\data\\1117\\'
    filename = directory + "test_SRS860.csv"
    pd.DataFrame(results).to_csv(filename, index=False)
    
    print('Test 1 done')
    time.sleep(5)
    
    #srs.experiment_setup(f)
    
    #print('Test 2 done, exp setup')



    # #plot of signal
    
    # srs = SRS830(gpib_address = 10)
    # srs.reset()
    # srs.set_output_amplitude(5)
    # srs.set_sensitivity(100e-6)
    # frequencies = np.logspace(-1, 7, 300)# spaces logarithmically from 10^-1 Hz to 1

    # t = np.linspace(0, 30, 10)

    # results = []

    # for f in frequencies:  #for f in frequencies:
    #     srs.set_output_frequency(f)
    #     time_const = 15/f
    #     srs.set_time_constant(time_const)
        
        
        
        
    #     R,theta, f_ref = srs.read_all()

    #     sensitivity = srs.get_sensitivity()
    #     if R/sensitivity < 0.1:
    #         srs.set_sensitivity(2*R)
    #     while R/sensitivity >= 1:
    #         srs.set_sensitivity(sensitivity*2)
    #         sensitivity = srs.get_sensitivity()
            
    #     time.sleep(max(2*time_const,0.1))
    #     R,theta, f_ref = srs.read_all()

    #     results.append(dict(
    #         f_ref = f_ref,
    #         R = R,
    #         theta = theta

    #     ))

    #     print(results[-1])

    # srs.set_output_frequency(1)
    # srs.set_output_amplitude(1e-5)
    

    # directory = 'C:\\Users\\Mossbauer\\Documents\\data\\20250416_piezo_transfer_functions\\'
    # filename = directory + "smallpiezo_glued_01.csv"

    # pd.DataFrame(results).to_csv(filename, index=False)
    
    # df = pd.DataFrame(results)
    # fig, ax = plt.subplots(2,1)
    # ax[0].semilogx(df['f_ref'], df['theta'])
    # ax[1].loglog(df['f_ref'], df['R'])
    # plt.show()
    