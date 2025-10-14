
import pyvisa
import time
import matplotlib.pyplot as plt 
import numpy as np
import csv 
import os
from pyvisa.constants import ControlFlow, Parity, StopBits
import pandas as pd


#from keithley_class import keithley
#from SRS830 import SRS830
#from bnc555 import bnc
#from K263 import K263
#from SRSDC205 import dc205
from DS360 import DS360

#bnc = bnc(gpib_address = 1)
#thermo = keithley(gpib_address = 6)
#voltmeter = keithley(gpib_address = 7)
#srs = SRS830(gpib_address = 10)
#calibrator = K263(gpib_address = 9)
drive = DS360(gpib_address = 8)
#dc205 = dc205()


#set up fast stage
#amp = 6.579
#offset_V = amp/2

#drive.set_sine()
drive.set_frequency(10)
#drive.set_amplitude(amp)
#drive.set_offset(offset_V)
#drive.output_on()



