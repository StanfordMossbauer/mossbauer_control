from cgitb import reset
import numpy as np
import RPi.GPIO as GPIO
import pyvisa
from time import sleep
import signal
import sys, os
from moku.instruments import WaveformGenerator, Oscilloscope
import configparser
import atexit

import logging

class StreamToLogger(object):
    """Fake file-like stream object that redirects writes to a logger instance.

    from https://stackoverflow.com/questions/19425736/how-to-redirect-stdout-and-stderr-to-logger-in-python
    """
    def __init__(self, logger, level):
       self.logger = logger
       self.level = level
       self.linebuf = ''
       return

    def write(self, buf):
       for line in buf.rstrip().splitlines():
          self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


# Establish a connection to a moku
class mokuGO:
    '''
    Class object to interact with a moku GO.

    Power Supply Channel 1 is used to generate the bias voltage to the PMT
    AO Channel 2 is used for square wave with 50% duty cycle
    to drive the stepper motor.

    Unfortunately, the API seems to require us to reconnect to the Moku every time
    we call it, which introduces ~10 seconds of deadtime. This should be improved.
    '''
    def __init__(self, ip:str):
        try:
            self.inst = WaveformGenerator(ip, force_connect=True)
            self.ip = ip
        except Exception as e:
            print(e)
            print(f'Unable to connect to Moku GO at {ip}')
            sys.exit()
        self.DUTY = 50           # Duty cycle
        self.AMP = 5             # Amplitude of pulse
        self.OFFSET = 2.5        # Makes a TTL like signal with the above amp
        return

    def setBaseHV(self, Vout:float, channel:int=1):
        '''
        DC voltage output to generate PMT HV with active base.

        Parameters:
        ------------
        Vout: float
            Desired control voltage [V]. HV is x1000.
            set to 0 to turn off
        channel: int
            Desired channel to use. Defaults to 1.

        Returns:
        --------
        Status message.
        '''
        self.osc = Oscilloscope(self.ip, force_connect=True)
        enable = False
        if Vout:
            enable = True
        self.osc.set_power_supply(
            channel,
            voltage=Vout,
            current=0.1,
            enable=enable
        )
        print(self.osc.get_power_supply(channel))
        self.osc.relinquish_ownership()
        self.inst = WaveformGenerator(self.ip, force_connect=True)  # reset API conn
        return

    def _setPWM(self, freq:float, channel: int=2):
        '''
        Turn on 50% duty cycle square wave with set frequency.

        Parameters:
        -------------
        freq: float
            Desired frequency.

        Returns:
        -------------
        Status message.
        '''
        #self.inst = WaveformGenerator(self.ip, force_connect=True)
        wftype = 'Off'
        if freq:
            wftype = 'Square'
        self.inst.generate_waveform(
            channel=channel,
            type=wftype,
            offset=self.OFFSET,
            amplitude=self.AMP,
            frequency=freq,
            duty=self.DUTY,
        )
        print(self.inst.summary())
        #self.inst.relinquish_ownership()
        return

    def PWMon(self, freq:float, channel: int=2):
        ''' Turn off 50% duty cycle square wave with set frequency.
        '''
        self._setPWM(freq, channel)
        return

    def PWMoff(self, channel: int=2):
        ''' Turn off 50% duty cycle square wave with set frequency.
        '''
        self._setPWM(0, channel)
        return
        

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
        motor_ctrl_serial = serial.Serial("COM6", 1000000)  # TODO: make this kwarg
        print(motor_ctrl_serial.readline())

        if self.vel/self.RES_1 > self.MAX_FREQ:
            print(f"You've requested a step frequency of {self.vel:.2f} Hz. Setting to {MAX_FREQ/1e3:.2f} kHz")
            self.fStep = self.MAX_FREQ
        else:
            self.fStep = self.vel/self.RES_1 # In Hz
        GPIO.output(self.AW_OFF, GPIO.LOW) # By default, turn off drive
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
        motor_ctrl_serial.write('f')
        print(f"CUT OFF current to all windings...")
        return

    def AWon(self):
        '''
        Function to ENABLE drive to the motor.
        '''
        motor_ctrl_serial.write('e')
        print(f"ENABLED current to all windings...")
        return
    
    def readCtrlState(self):
        motor_ctrl_serial.write('?')
        print(motor_ctrl_serial.readline())
        return

    def __del__(self):
        motor_ctrl_serial.close()


class ScanController:
    def __init__(self, **kwargs):
        default_config = dict(
            mokuWGChannel=2,
            commandSleepTime=0,  # s
            scanTravelDist=40,  # mm
            returnVelocity=5,  # mm/s
            logfileName='scan.log',
            fullLength=180,  # mm
        )
        for key, val in default_config.items():
            setattr(self, key, kwargs.get(key, val))
        self.log_output(self.logfileName)

        self.moku = mokuGO(kwargs.get('mokuIP', '192.168.73.1'))

        self.ctrl = DFR1507A()
        self.stopMotion()
        atexit.register(self.stopMotion)
        return


    def log_output(self, logfile):
        logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s:%(levelname)s:\t%(message)s',
                handlers=[
                    logging.FileHandler(logfile),
                    logging.StreamHandler()
                ],
                )
        log = logging.getLogger('scanlog')
        sys.stdout = StreamToLogger(log, logging.INFO)
        sys.stderr = StreamToLogger(log, logging.ERROR)
        return

    def start_step(self, vel, res=1):
        self.ctrl.setResolution(res)
        self.ctrl.setVelocity(vel)
        self.moku.PWMon(self.ctrl.fStep, self.mokuWGChannel)
        self.ctrl.AWon()
        return

    def step(self, vel, dist, res=1):
        """Step for dist mm at vel mm/s
        """
        tStep = dist/np.abs(vel)
        self.start_step(vel, res)
        sleep(self.commandSleepTime)
        sleep(tStep)
        self.stopMotion()
        return

    def quickReturn(self, vel):
        self.step(
            -1 * self.returnVelocity * np.sign(vel),
            self.scanTravelDist, 
            2
        )
        return
        
    def scan(self, vel):
        '''
        Initiate a scan at some velocity.

        Parameters:
        --------------
        vel: float
            Velocity in mm/sec.

        Returns:
        ---------
        Nothing.
        
        '''
        self.step(vel, self.scanTravelDist)
        # And then go back to where we started.
        self.step(
            -1 * self.returnVelocity * np.sign(vel),
            self.scanTravelDist, 
            2
        )
        return

    def stopMotion(self):
        '''
        Function to stop all motion and turn off TTL output from the function generator.
        Returns:
        ---------
        Nothing.
        '''
        self.ctrl.AWoff()
        self.moku.PWMoff(self.mokuWGChannel)
        self.ctrl.setResolution(1)  # I think we want this...
        return

    def resetZeroPosition(self, **kwargs):
        '''
        Return all the way to starting position.
        First move toward source by (kwarg currentPosition, 
        defaults to full length), then move back by kwarg
        startPosition (defaults to scanTravelDist plus a buffer cm)
        '''
        currentPosition = kwargs.get('currentPosition', self.fullLength)
        startPosition = kwargs.get('startPosition', self.scanTravelDist + 10.)
        self.step(self.returnVelocity, currentPosition)
        self.step(-1*self.returnVelocity, startPosition)
        return


if __name__=='__main__':
    scan = ScanController()
    # Turn on the base high voltage
    scan.moku.setBaseHV(1, 1) # Default to 1kV bias on channel 1
