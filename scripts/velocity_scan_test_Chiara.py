#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 14:01:10 2025

@author: chiarabrandenstein
"""

import time
from mossbauer_control.instruments import DS360
import numpy as np

drive = DS360(gpib_address = 8)

def vmax(A=3.3, f=40, k=0.118*1e-6): #k given in m/V for big piezo
                                        #with given values it is at 0.1mm/s
    return A*2*np.pi*f*k

#we want to just type in a velocity and it sets up the stage
def set_to_v(v, f =40, k= 0.118*1e-6): #type in v in SI units
    A = v/(2*np.pi*f*k)
    print(v*1e3)
    print(A)
    offset = A/2
    drive.set_sine()
    drive.set_frequency(f)
    drive.set_amplitude(A)
    drive.set_offset(offset)
    drive.output_on()
    
#then we can scan velocities
velocities = np.arange(0.1*1e-3, 0.7*1e-3, 0.1*1e-3)

for velocity in velocities:
    set_to_v(velocity)
    time.sleep(5)
    #print('v=', velocity*1e3)