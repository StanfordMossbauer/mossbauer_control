# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 15:48:47 2023

@author: Albert
"""

import serial
ser = serial.Serial("COM6", 1000000)
print(ser.readline())
ser.write('a')
print(ser.readline())
ser.write('?')
print(ser.readline())
ser.close()
class DFR1507A:
    def __init__(self, DIR: str='CCW', RES: int=1, vel: float=0):
        motor_ctrl_serial = serial.Serial("COM6", 1000000)
        print(motor_ctrl_serial.readline())

    def setResolution(self, res: int):
        '''
        Funtion to select the resolution of steps, based on the RS1/2 dials on the DFR1507A.
        
        Parameters:
        -----------
        res: int
            Resolution setting to use. Must be "1" or "2".

        Returns:
        ---------
        Nothing.
        '''
        if res==1:
            motor_ctrl_serial.write('a')
        elif res==2:
            motor_ctrl_serial.write('b')
        else:
            print(f"You requested for {res}, please specify either 1 or 2.")
        self.RES=res
        print(f"Using resolution set by RS{self.RES}")
        return

    def setDirection(self, DIR: str):
        '''
        Function to select the direction of rotation.

        Parameters:
        -------------
        DIR: str
            Direction of rotation. Must be "CW" or "CCW".
        '''
        if DIR=='CW':
            motor_ctrl_serial.write('c')
        elif DIR=='CCW':
            motor_ctrl_serial.write('d')
        else:
            print(f"You requested for {DIR} rotation, please specify either 'CW' or 'CCW'.")
        self.DIR=DIR
        print(f"Direction of rotation is {self.DIR}")
        return

    def AWon(self):
        '''
        Function to ENABLE drive to the motor.
        '''
        motor_ctrl_serial.write('e')
        print(f"ENABLED current to all windings...")
        return()

    def AWoff(self):
        '''
        Function to DISABLE drive to the motor.
        '''
        motor_ctrl_serial.write('f')
        print(f"CUT OFF current to all windings...")
        return()
    
    def readCtrlState(self):
        motor_ctrl_serial.write('?')
        print(motor_ctrl_serial.readline())
        return()

    def __del__(self):
        motor_ctrl_serial.close()

if __name__ == "__main__":
    ser = serial.Serial("COM6", 1000000)
    print(ser.readline())
    ser.write('a')
    print(ser.readline())
    ser.write('?')
    print(ser.readline())
    ser.close()
    