# SRS830 Programming Manual: https://www.thinksrs.com/downloads/pdfs/manuals/SR830m.pdf
import pyvisa
import matplotlib.pyplot as plt
import numpy as np
import time
import pandas as pd

# Time constants are in seconds
TIME_CONSTANTS = {
    0: 10e-6, 1: 30e-6, 2: 100e-6, 3: 300e-6, 4: 1e-3, 5: 3e-3, 6: 10e-3,
    7: 30e-3, 8: 100e-3, 9: 300e-3, 10: 1, 11: 3, 12: 10, 13: 30, 14: 100,
    15: 300, 16: 1e3, 17: 3e3, 18: 10e3, 19: 30e3
}

# Sensitivities are in volts
SENSITIVITIES = {
    0: 2e-9, 1: 5e-9, 2: 10e-9, 3: 20e-9, 4: 50e-9, 5: 100e-9, 6: 200e-9,
    7: 500e-9, 8: 1e-6, 9: 2e-6, 10: 5e-6, 11: 10e-6, 12: 20e-6, 13: 50e-6,
    14: 100e-6, 15: 200e-6, 16: 500e-6, 17: 1e-3, 18: 2e-3, 19: 5e-3,
    20: 10e-3, 21: 20e-3, 22: 50e-3, 23: 100e-3, 24: 200e-3, 25: 500e-3,
    26: 1, 27: 2, 28: 5, 29: 10, 30: 20, 31: 50
}


class SRS830:
    def __init__(self, gpib_address=10):
        self.gpib_address = gpib_address
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(f"GPIB::{gpib_address}", )
        self.instrument.baud_rate = 9600
        self.instrument.write("SEND 0") #shot mode (1 for loop mode)


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

    def read_all(self):
        res = self.instrument.query("SNAP? 3,4,9")
        R, theta, f_ref = np.array(res[:-1].split(",")).astype('float')
        return R, theta, f_ref 

    def reset(self):
        self.instrument.write('REST')
    
    #clear buffer
    #set reference (internal or extenal)

    def close(self):
        self.instrument.close()
        self.rm.close()
    
    def experiment_setup(self,time_const=10):
        self.reset()
        self.set_sensitivity(100) #added
        self.set_time_constant(time_const)



if __name__ == "__main__":
    #run for 40Hz drive
    srs = SRS830(gpib_address = 10)
    srs.reset()
    srs.set_sensitivity(100) #added
    results = []
    f=40
    time_const = 15/f
    srs.set_time_constant(time_const)
    i = 0
    while i <10000:
        R,theta, f_ref = srs.read_all()

        results.append(dict(
            f_ref = f_ref,
            R = R,
            theta = theta
            ))
        i+=1

    directory = 'C:\\Users\\Mossbauer\\Documents\\data\\0917\\'
    filename = directory + "test_SRS830.csv"

    pd.DataFrame(results).to_csv(filename, index=False)



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
    