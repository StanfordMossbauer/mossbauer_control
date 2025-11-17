import pyvisa
import time
import matplotlib.pyplot as plt 
import numpy as np
import csv 
import os
from pyvisa.constants import ControlFlow, Parity, StopBits
import pandas as pd
from datetime import datetime

from mossbauer_control.instruments import keithley
from mossbauer_control.instruments import SRS830
from mossbauer_control.instruments import dc205

#or we can create a new csv file every day
def get_file_path(base_dir):
    """Generate file path with current date"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"RTD_{date_str}.csv"
    return os.path.join(base_dir, filename)

# Folder to save CSVs
base_dir = r'C:\Users\mossbauer\Documents\data\1117'
os.makedirs(base_dir, exist_ok=True)

# Track current file date
current_day = datetime.now().date()
file_path = get_file_path(base_dir)

dc205 = dc205()
thermo = keithley(gpib_address = 7)

# thermo.set_voltage_mode()
# thermo.clear_buffer()
# thermo.store_raw_readings()
# thermo.cont_operation()
# thermo.initialize()

dc205.output_on()

voltage = 2
switch_interval = 10 
read_interval = 1   

start_time = time.time()
last_switch_time = start_time

while True:
    now = datetime.now()
    if now.date() != current_day:
        # New day, create a new file
        current_day = now.date()
        file_path = get_file_path(base_dir)
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['time', 'diff_T', 'abs_T', 'voltage'])

    current_time = time.time()

    # if current_time - last_switch_time >= switch_interval:
    #     voltage = -voltage 
    #     dc205.set_voltage(voltage)
    #     last_switch_time = current_time

    # Generate voltage list from 0–2 V in 0.1 V steps
    voltages = np.arange(0, 2.1, 0.1)   # includes 2.0 V

    for voltage in voltages:
        dc205.set_voltage(voltage)
        time.sleep(5)                   # settling time after voltage change

        for _ in range(60):             # 60 seconds of measurement
            ch1, ch2 = thermo.measure_both()
            diff_T = ch1
            abs_T = ch2
            timestamp = time.time()

            with open(file_path, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([timestamp, diff_T, abs_T, voltage])




    # ch1, ch2 = thermo.measure_both()
    
    # diff_T = ch1
    # abs_T = ch2

    #print(diff_T, abs_T)

    

    # timestamp = time.time()
    # with open(file_path, mode='a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow([timestamp, diff_T, abs_T])


