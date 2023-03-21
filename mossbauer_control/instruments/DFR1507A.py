"""
This was taken from Gautam's old code and was specifically for controlling
the stepper through the MokuGo. It is no longer used in the current setup.
"""

class DFR1507A:
    '''
    Initiates an instance of the DFR1507A driving a KR26.
    '''
    def __init__(self, DIR: str='CCW', RES: int=1, vel: float=0):
        '''
        Init function. 

        Parameters:
        ------------
        DIR: str
            Direction of motor rotation. Defaults to 'CCW'.
            Must be either 'CCW' or 'CW'.
        RES: int

        '''
        # ugly hardcoding
        RES_1 = 2*0.00288/360 # (ball screw lead mm/rev) * (?) / 1rev
        RES_2 = 2*0.009/360 # (ball screw lead mm/rev) * (?) / 1rev
        DIR_SELECT = 24  # Direction select. 0=CW, 1=CCW
        RES_SELECT = 16  # res select. 0=RS1, 1=RS2
        AW_OFF = 25      # All windings off pin. 0=no drive. 1= regular drive
        MAX_FREQ = 500e3    # Don't pulse faster than this. Controller technically can handle up to 1MHz.

        self.__dict__.update(locals())

        # connect to arduino
        self.arduino_serial = serial.Serial("/dev/ttyACM0", 1000000)  # TODO: make this kwarg
        print(self.arduino_serial.readline())

        if self.vel/self.RES_1 > self.MAX_FREQ:
            print(f"You've requested a step frequency of {self.vel:.2f} Hz. Setting to {MAX_FREQ/1e3:.2f} kHz")
            self.fStep = self.MAX_FREQ
        else:
            self.fStep = self.vel/self.RES_1 # In Hz
        self.AWoff()
        return
        

    def cleanup(self):
        '''
        Re-initializes the GPIO pins and frees them. 
        '''
        GPIO.cleanup()
        return()
    
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
            self.arduino_serial.write('a')
        elif res==2:
            self.arduino_serial.write('b')
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
            self.arduino_serial.write('c')
        elif DIR=='CCW':
            self.arduino_serial.write('d')
        else:
            print(f"You requested for {DIR} rotation, please specify either 'CW' or 'CCW'.")
        self.DIR=DIR
        print(f"Direction of rotation is {self.DIR}")
        return

    def setVelocity(self, vel: float):
        '''
        Function to set the linear velocity.

        Parameters:
        -------------
        vel: float
            Linear velocity in mm/s. A positive value results in CCW rotation, while a negative value results in CW rotation

        Returns:
        ----------
        Nothing.
        '''
        if vel>0:
            self.setDirection('CCW')
        else:
            self.setDirection('CW')
        vel = abs(vel)
        if self.RES==1:
            self.fStep = vel/self.RES_1 # In Hz
        else:
            self.fStep = vel/self.RES_2
        print(f"Setting velocity to {vel:.3f}mm/sec, stepping at {self.fStep:3f}Hz")
        return
    
    def AWoff(self):
        '''
        Function to DISABLE drive to the motor.
        '''
        self.arduino_serial.write('f')
        print(f"CUT OFF current to all windings...")
        return

    def AWon(self):
        '''
        Function to ENABLE drive to the motor.
        '''
        self.arduino_serial.write('e')
        print(f"ENABLED current to all windings...")
        return
    
    def readCtrlState(self):
        self.arduino_serial.write('?')
        print(self.arduino_serial.readline())
        return

    def __del__(self):
        self.arduino_serial.close()
