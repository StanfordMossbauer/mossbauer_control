'''
Set of functions to interact with a stepper motor 
in the Mössbauer lab. This particular piece of code
has been superseded by a version that uses a MokuGo
as a function generator.
'''

from cgitb import reset
import numpy as np
import RPi.GPIO as GPIO
import pyvisa
from time import sleep
import signal, sys
from moku.instruments import WaveformGenerator

#################
## STAGE CONFIG #
BALL_SCREW_LEAD = 6 # mm, ball screw lead
RES_1 = 0.00288 
RES_2 = 0.009
RES_1 = BALL_SCREW_LEAD*RES_1/360 # in mm
RES_2 = BALL_SCREW_LEAD*RES_2/360 # in mm
D_TRAVEL = 50 # mm of travel
V_RETURN = 5 # mm/sec at which to return to starting pos
## STAGE CONFIG #
#################
#################
## GPIO CONFIG #
DIR_SELECT = 24  # Direction select. 0 = CW, 1=CCW
RES_SELECT = 16  # res select. 0 = RS1, 1 = RS2
AW_OFF = 25      # All windings off pin. 0 = no drive. 1= regular drive
#################

#################
## FUNC GEN CONFIG #
DUTY = 50           # Duty cycle
MAX_FREQ = 500e3    # Don't pulse faster than this. Controller technically can handle up to 1MHz.
LOAD = 'HZ'         # Hi Z load by default.
WAVEFORM = 'PULSE'  # Type of waveform
AMP = 5             # Amplitude of pulse
OFFSET = 2.5        # Makes a TTL like signal with the above amp

#################

#####################
# A CTRL-C HANDLER  #
def signal_handler(*args):
    stopMotion(ctrl, funcGen)
    print('You pressed Ctrl+C!')
#####################


# Clean up any residual connections
GPIO.cleanup()
# Setup the pins...
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_SELECT,GPIO.OUT)
GPIO.setup(RES_SELECT,GPIO.OUT)
GPIO.setup(AW_OFF,GPIO.OUT)


# Establish connection to the func gen
class BK4054:
    '''
    Class object to interact with the BK Precision 4054B signal generator,
    over a USB connection.
    '''
    def __init__(self, resource):
        '''
        Initialize a connection, and set up the unit to generate the appropriate
        TTL logic level signals.
        '''
        try:
            self.inst = pyvisa.ResourceManager('@py').open_resource(resource)
            idn = self.inst.query('*IDN?')
            print(f'Connected to {idn}')
            #Setup channel 1 for use
            self.inst.write('C2:OUTP OFF')
            sleep(0.5)
            self.inst.write(f'C2:LOAD {LOAD}')
            sleep(0.5)
            self.inst.write(f'C2:BSWV WVTP,{WAVEFORM}')
            sleep(0.5)
            self.inst.write('C2:BSWV FRQ,1000')
            sleep(0.5)
            self.inst.write(f'C2:BSWV AMP,{AMP}')
            sleep(0.5)
            self.inst.write(f'C2:BSWV OFST,{OFFSET}')
            sleep(0.5)
            self.inst.write(f'C2:BSWV DUTY,{DUTY}')
        except Exception as e:
            print(e)
    
    def query(self,cmd:str):
        '''
        Function to query BK4054B.
        
        Parameters:
        ------------
        cmd: str
            Command string - see manual.
        
        Returns:
        --------
        retStr: str
            Return string from device. See manual.
        '''
        retStr = self.inst.query(cmd)
        print(retStr)
        return

    def setFreq(self, freq: float, channel: int=2):
        '''
        Function to set the frequency of the TTL pulse.

        Parameters:
        ------------
        freq: float
            Desired frequency [Hz]
        channel: int
            Channel on signal generator. Must be "1" or "2".
            Defaults to 1.

        Returns:
        ------------
        Nothing.
        '''
        if channel>2:
            print(f"You requested to change frequency of Channel {channel} which is not supported. Use '1' or '2'.")
        self.inst.write(f'C{channel}:BSWV FRQ, {freq}Hz')
        print(self.inst.query(f'C{channel}:BSWV?'))
        return
    def outputOn(self, channel: int=2):
        '''
        Function to ENABLE output.

        Parameters:
        -----------
        channel: int
            Channel to enable output. Defaults to Channel 1.

        Returns:
        ---------
        Nothing.
        '''
        if channel>2:
            print(f"You requested to enable Channel {channel} which is not supported. Use '1' or '2'.")
        self.inst.write(f'C{channel}:OUTP ON')
        return()
    def outputOff(self, channel: int=2):
        '''
        Function to DISABLE output.

        Parameters:
        -----------
        channel: int
            Channel to disable output. Defaults to Channel 1.

        Returns:
        ---------
        Nothing.
        '''
        if channel>2:
            print(f"You requested to disable Channel {channel} which is not supported. Use '1' or '2'.")
        self.inst.write(f'C{channel}:OUTP OFF')
        return()



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
        self.__dict__.update(locals())
        if self.vel/RES_1 > MAX_FREQ:
            print(f"You've requested a step frequency of {self.vel:.2f} Hz. Setting to {MAX_FREQ/1e3:.2f} kHz")
            self.fStep = MAX_FREQ
        else:
            self.fStep = self.vel/RES_1 # In Hz
        GPIO.output(AW_OFF, GPIO.LOW) # By default, turn off drive
        

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
            GPIO.output(RES_SELECT,GPIO.HIGH)
        elif res==2:
            GPIO.output(RES_SELECT,GPIO.LOW)
        else:
            print(f"You requested for {res}, please specify either 1 or 2.")
        self.RES=res
        print(f"Using resolution set by RS{self.RES}")
        return()

    def setDirection(self, DIR: str):
        '''
        Function to select the direction of rotation.

        Parameters:
        -------------
        DIR: str
            Direction of rotation. Must be "CW" or "CCW".
        '''
        if DIR=='CW':
            GPIO.output(DIR_SELECT,GPIO.HIGH)
        elif DIR=='CCW':
            GPIO.output(DIR_SELECT,GPIO.LOW)
        else:
            print(f"You requested for {DIR} rotation, please specify either 'CW' or 'CCW'.")
        self.DIR=DIR
        print(f"Direction of rotation is {self.DIR}")
        return()

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
            self.fStep = vel/RES_1 # In Hz
        else:
            self.fStep = vel/RES_2
        print(f"Setting velocity to {vel:.3f}mm/sec, stepping at {self.fStep:3f}Hz")
        return()
    
    def AWoff(self):
        '''
        Function to DISABLE drive to the motor.
        '''
        GPIO.output(AW_OFF,GPIO.LOW)
        print(f"CUT OFF current to all windings...")
        return()

    def AWon(self):
        '''
        Function to ENABLE drive to the motor.
        '''
        GPIO.output(AW_OFF,GPIO.HIGH)
        print(f"ENABLED current to all windings...")
        return()

def scan(ctrl, funcGen, vel: float=0):
    '''
    Initiate a scan at some velocity.

    Parameters:
    --------------
    ctrl: DFR1507A class object
        The controller.
    funcGen: BK4054B class object.
        BK4054B controlled over USB.
    vel: float
        Velocity in mm/sec.

    Returns:
    ---------
    Nothing.
    
    '''
    if vel<0:
        returnVel = V_RETURN
    else:
        returnVel = -V_RETURN
    tScan = D_TRAVEL/np.abs(vel) # seconds to scan
    tReturn = D_TRAVEL/V_RETURN
    ctrl.setVelocity(vel)
    funcGen.setFreq(ctrl.fStep)
    ctrl.AWon()
    sleep(1)
    funcGen.outputOn()
    sleep(tScan)
    ctrl.AWoff()
    funcGen.outputOff()
    # And then go back to where we started.
    ctrl.setResolution(2)
    ctrl.setVelocity(returnVel)
    # if ctrl.DIR=='CCW':
    #     ctrl.setVelocity(-V_RETURN)
    funcGen.setFreq(ctrl.fStep)
    ctrl.AWon()
    sleep(1)
    funcGen.outputOn()
    sleep(tReturn)
    funcGen.outputOff()
    ctrl.AWoff()
    sleep(1)
    ctrl.setResolution(1) # Reset to the fine scan...
    return

def stopMotion(ctrl, funcGen):
    '''
    Function to stop all motion and turn off TTL output from the function generator.

    Parameters:
    --------------
    ctrl: DFR1507A class object
        The controller.
    funcGen: BK4054B class object.
        BK4054B controlled over USB.
    vel: float
        Velocity in mm/sec.

    Returns:
    ---------
    Nothing.
    '''
    ctrl.AWoff()
    funcGen.outputOff()
    return
    




# Connect to the func gen
rm = pyvisa.ResourceManager('@py')
res = rm.list_resources()[0]
funcGen = BK4054(res)

ctrl = DFR1507A()
ctrl.AWoff()
ctrl.setDirection('CCW')
ctrl.setResolution(1)
ctrl.setVelocity(0.5) # mm/s
signal.signal(signal.SIGINT, signal_handler)

