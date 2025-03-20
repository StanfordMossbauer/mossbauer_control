import numpy as np
import time
import sys, os

#from mossbauer_control.spectrometer import MossbauerSpectrometer
from mossbauer_control.spectrometer2 import MossbauerSpectrometer


frequencies = np.linspace(0, 1.5, 25)  # standard 25pts
#frequencies = np.array([0.365, 0.135])  # manually converted (FeCy 2pts, v=0.232, 0.086 mm/s)
#frequencies = np.ones(2)
repetitions = 10
#repetitions = 3

directory = "/home/mossbauer/Data/mossbauer_data/{}_scan/".format(time.strftime("%Y%m%d"))
#data_file = directory + 'Fe0004_0.9_mms_25steps_0.6-17in.dat'
data_file = directory + 'FeCy_0.25_mms_2steps_0.5-1in.dat'
#data_file = directory + 'test2'
if not os.path.isdir(directory):
    os.mkdir(directory)

protect_overwrite = True
if protect_overwrite:
    ## avoids overwriting
    if os.path.isfile(data_file): 
        print('filename exists choose another one!') 
        sys.exit()

scan = MossbauerSpectrometer()
scan.scan(frequencies, repetitions, data_file)
