import pyvisa
import time 
import numpy as np
import csv 
import os
from pyvisa.constants import ControlFlow, Parity, StopBits
import pandas as pd
from datetime import datetime


from keithley_class import keithley

thermo = keithley(gpib_address = 7)

# thermo.write("*RST")
# thermo.write("STAT:PRES;*CLS")
# thermo.write("STAT:MEAS:ENAB 512")
# thermo.write("*SRE 1")
# thermo.write("TRIG:COUN 10")
# thermo.write(":TRAC:POIN 10")
# thermo.write(":TRAC:FEED SENS1")
# thermo.write(":TRAC:FEED:CONT NEXT")
# thermo.write(":INIT")

# time.sleep(1)

# raw = thermo.query("TRAC:DATA?")

def get_buffer_data():
    thermo.write("*RST")
    thermo.write("STAT:PRES;*CLS")
    thermo.write("STAT:MEAS:ENAB 512")
    thermo.write("*SRE 1")
    thermo.write("TRIG:COUN 10")
    thermo.write(":TRAC:POIN 10")
    thermo.write(":TRAC:FEED SENS1")
    thermo.write(":TRAC:FEED:CONT NEXT")
    thermo.write(":INIT")

    time.sleep(1)

    raw = thermo.query("TRAC:DATA?")

    return raw

data = get_buffer_data()

data2 = thermo.use_buffer()