import pyvisa
import time
import matplotlib.pyplot as plt 
import numpy as np
import csv 
import os
from pyvisa.constants import ControlFlow, Parity, StopBits
import pandas as pd

#https://www.tek.com/en/products/keithley/low-level-sensitive-and-specialty-instruments/nanovoltmeter-model-2182a

class keithley:
    def __init__(self, gpib_address=7):
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
    
    def read(self):
        r = float(self.instrument.query(":READ?"))
        return r

    def query(self, string):
        r = self.instrument.query(string)
        return r

    def run(self):
        self.write("RUN")

    def stop(self):
        self.write('STOP')

    def set_voltage_mode(self):
        self.write("CONF:VOLT")

    def reset(self):
        self.write("*RST")

    def reset_subsys(self):
        self.write("STAT:PRES;*CLS")

    def enable_buffer(self):
        self.write("STAT:MEAS:ENAB 512")
    
    def enable_msb(self):
        self.write("*SRE 1")

    def set_trigger_count(self, number = 10):
        self.write(f"TRIG:COUN {number}")

    def data_ascii(self):
        self.write(":FORM:DATA ASCII")

    def filter_off(self):
        self.write(':SENS:VOLT:DC:DFIL:STAT OFF')

    def filter_on(self, samples): #samples can be between 1-100, will be averaged over
        self.write(f':SENS:VOLT:DC:DFIL:COUN {samples}')

    def set_delay_trigger(self, t): #given in seconds
        self.write(f'TRIG:DEL {t}')

    def sample_count(self, n=1): #sets the number of samples stored in the buffer 1-1024
        self.write(f':SAMP:COUN {n}')

    def read_rate(self, rate=1): #sets the measurement time PLC on the keithley, for slow set it to (0.1-5)
        self.write(f':SENS:VOLT:DC:NPLC {rate}')

    def clear_buffer(self):
        self.write(":TRAC:CLE")

    def set_buffer_size(self, n=1):
        self.write(f":TRAC:POIN {n}")

    def store_raw_readings(self, channel = 1):
        self.write(f":TRAC:FEED SENS{channel}")
    
    def wait_for_buffer(self):
        self.write(":TRAC:FEED:CONT NEXT")

    def get_data(self):
        data = float(self.query(":FETCH?"))
        return data
   
    def cont_operation(self, status='ON'): #status can be ON or OFF
        self.write(f":INIT:CONT {status}")

    def initialize(self): #remove it from idle state
        self.write(":INIT")

    def get_buffer_data(self):
        self.query("TRAC:DATA?")

    def set_channel(self,chan):
        self.write(f":SENS:CHAN {chan}")

     


    def buffer_data(self):
        self.write("*RST")
        self.write("STAT:PRES;*CLS")
        self.write("STAT:MEAS:ENAB 512")
        self.write("*SRE 1")
        self.write("TRIG:COUN 10")
        self.write(":TRAC:POIN 10")
        self.write(":TRAC:FEED SENS1")
        self.write(":TRAC:FEED:CONT NEXT")
        self.write(":INIT")
        time.sleep(1)

        raw = self.query("TRAC:DATA?")

        return raw

    def measure_both(self):  #not averaged
        self.write(":INIT:CONT OFF")

        self.write(":SENS:CHAN 2")
        time.sleep(1)
        ch2_reading = float(self.query(":READ?"))
        print(ch2_reading)
        time.sleep(1)
        self.write(":SENS:CHAN 1")
        time.sleep(1)
        ch1_reading = float(self.query(":READ?"))
        print(ch1_reading)
        
        return ch1_reading, ch2_reading
    
    def measure_both_v2(self):  #not averaged
        self.cont_operation(status='OFF')

        self.set_channel(1)
        time.sleep(0.04)
        ch1_reading = self.read()
        self.set_channel(2)
        time.sleep(0.04)
        ch2_reading = self.read()
        #print(ch2_reading)
        
        return ch1_reading, ch2_reading
    
    def measure_both_v3(self):  #not averaged
        self.cont_operation(status='OFF')

        self.set_channel(1)
        time.sleep(0.1)

        for i in range(10):
            t =time.time()
            ch1_reading = self.read()
            print(ch1_reading, time.time()-t)
        time.sleep(0.1)
        self.set_channel(2)
        time.sleep(0.1)
        ch2_reading = self.read()
        print(ch2_reading)
        
        return ch1_reading, ch2_reading
    
    def experimental_voltmeter_setup(self): 
        self.set_voltage_mode()
        self.clear_buffer()
        self.store_raw_readings()
        self.cont_operation()
        self.initialize()
        
    def experimental_thermo_setup(self):
        return 
    

if __name__=='__main__':

    thermo = keithley(gpib_address = 7)
    result = thermo.measure_both_v2()
    #print(result)



    # 
    

    
    # voltmeter.set_voltage_mode()

    # voltmeter.clear_buffer()
    # voltmeter.store_raw_readings()
    # voltmeter.cont_operation()
    # voltmeter.initialize()
    
    # data_list = []
    # timestamps = []
    # start = time.time()

    # i = 1
    # while i<10:
    #     i+=1
    #     time.sleep(1)
    #     data = voltmeter.get_data()
    #     data_list.append(data)
    #     timestamps.append(time.time()-start)

    # df=pd.DataFrame(
    #     {'time':timestamps,
    #     'data':data_list}
    # )


    # # Define the full file path
    # save_path = r'C:\Users\mossbauer\Documents\data\0811\test_trigger.csv'
    # os.makedirs(os.path.dirname(save_path), exist_ok=True)
    # df.to_csv(save_path, index=False)

    # plt.plot(timestamps, data_list, color = 'purple')
    # plt.show()

    #when also measuring thermocouples


    #thermo = keithley(gpib_address = 7)
    #voltmeter = keithley(gpib_address = 6)
    #thermo.set_voltage_mode()
    #voltmeter.set_voltage_mode()

    #voltmeter.clear_buffer()
    #voltmeter.store_raw_readings()
    # voltmeter.cont_operation()
    # voltmeter.initialize()

    # thermo.clear_buffer()
    # thermo.store_raw_readings()
    # thermo.cont_operation()
    # thermo.initialize()
    
    # data_V = []
    # data_T = []
    # timestamps = []
    # start = time.time()

    # i = 1
    # while i<60:
    #     i+=1
    #     time.sleep(1)
    #     data = voltmeter.get_data()
    #     data_V.append(data)
    #     data = thermo.get_data()
    #     data_T.append(data)
    #     timestamps.append(time.time()-start)

    # df=pd.DataFrame(
    #     {'time':timestamps,
    #     'data V':data_V,
    #     'data T': data_T}
    # )


    # # Define the full file path
    # save_path = r'C:\Users\mossbauer\Documents\data\0929\keithley_01.csv'
    # os.makedirs(os.path.dirname(save_path), exist_ok=True)
    # df.to_csv(save_path, index=False)

    # plt.plot(timestamps, data_V, color = 'pink', label = 'strain')
    # plt.plot(timestamps, data_T, color = 'purple', label = 'T')
    # plt.legend()
    # plt.show()







  

    