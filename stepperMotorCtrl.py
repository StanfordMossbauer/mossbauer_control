from cgitb import reset
import numpy as np
import RPi.GPIO as GPIO
import pyvisa
from time import sleep
import signal, sys
from moku.instruments import WaveformGenerator, Oscilloscope


#################
## STAGE CONFIG #
BALL_SCREW_LEAD = 2 # mm, ball screw lead
RES_1 = 0.00288 
RES_2 = 0.009
RES_1 = BALL_SCREW_LEAD*RES_1/360 # in mm
RES_2 = BALL_SCREW_LEAD*RES_2/360 # in mm
D_TRAVEL = 40 # mm of travel
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
    stopMotion(ctrl, moku)
    print('You pressed Ctrl+C!')
#####################


# Clean up any residual connections
GPIO.cleanup()
# Setup the pins...
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_SELECT,GPIO.OUT)
GPIO.setup(RES_SELECT,GPIO.OUT)
GPIO.setup(AW_OFF,GPIO.OUT)
# GPIO.setup(DRIVE,GPIO.OUT)

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
    def summary(self):
        '''
        Print configuration status of the Moku Waveform Generator.
        '''
        self.inst = WaveformGenerator(self.ip, force_connect=True)
        print(self.inst.summary())
        return
    def BaseHVon(self, Vout:float, channel:int=1):
        '''
        DC voltage output to generate PMT HV with active base.

        Parameters:
        ------------
        Vout: float
            Desired control voltage [V]. HV is x1000.
        channel: int
            Desired channel to use. Defaults to 1.

        Returns:
        --------
        Status message.
        '''
        self.osc = Oscilloscope(self.ip, force_connect=True)
        self.osc.set_power_supply(channel,voltage=Vout, current=0.1, enable=True)
        print(self.osc.get_power_supply(channel))
        self.osc.relinquish_ownership()
        return
    def BaseHVoff(self, Vout:float, channel: int=1):
        '''
        Turn off PS 1.

        Parameters:
        ------------
        channel: int
            Power supply # to disable. Defaults to 1.
        Returns:
        --------
        Status message.
        '''
        self.osc = Oscilloscope(self.ip, force_connect=True)
        self.osc.set_power_supply(channel, enable=False)
        print(self.osc.get_power_supply(channel))
        self.osc.relinquish_ownership()
        return
    def PWMon(self, freq:float, channel: int=2):
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
        self.inst = WaveformGenerator(self.ip, force_connect=True)
        self.inst.generate_waveform(channel=channel, type='Square', offset=OFFSET, amplitude=AMP, frequency=freq, duty=DUTY)
        print(self.inst.summary())
        self.inst.relinquish_ownership()
        return()
    def PWMoff(self, channel: int=2):
        '''
        Turn off 50% duty cycle square wave with set frequency.

        Parameters:
        -------------
        freq: float
            Desired frequency.

        Returns:
        -------------
        Status message.
        '''
        self.inst = WaveformGenerator(self.ip, force_connect=True)
        self.inst.generate_waveform(channel=channel, type='Square', offset=0, amplitude=0, duty=DUTY)
        print(self.inst.summary())
        self.inst.relinquish_ownership()
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

def scan(ctrl, moku, vel: float=0):
    '''
    Initiate a scan at some velocity.

    Parameters:
    --------------
    ctrl: DFR1507A class object
        The controller.
    moku: mokuGO class object
        Moku GO.
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
    moku.PWMon(ctrl.fStep, 2) # Defaults to use channel 2
    ctrl.AWon() 
    sleep(1)
    sleep(tScan)
    ctrl.AWoff()
    moku.PWMoff(2)
    # And then go back to where we started.
    ctrl.setResolution(2)
    ctrl.setVelocity(returnVel)
    moku.PWMon(ctrl.fStep,2)
    ctrl.AWon()
    sleep(1)
    sleep(tReturn)
    moku.PWMoff()
    ctrl.AWoff()
    sleep(1)
    ctrl.setResolution(1) # Reset to the fine scan...
    return

def stopMotion(ctrl, moku):
    '''
    Function to stop all motion and turn off TTL output from the function generator.

    Parameters:
    --------------
    ctrl: DFR1507A class object
        The controller.
    moku: MokuGo class object.
        Moku Go object.
    vel: float
        Velocity in mm/sec.

    Returns:
    ---------
    Nothing.
    '''
    ctrl.AWoff()
    moku.PWMoff(2)
    return
    


# Connect to the moku
moku = mokuGO('192.168.73.1')
# Turn on the base high voltage
moku.BaseHVon(1,1) # Default to 1kV bias on channel 1

ctrl = DFR1507A()
ctrl.AWoff()
ctrl.setDirection('CCW')
ctrl.setResolution(1)
ctrl.setVelocity(0.5) # mm/s
signal.signal(signal.SIGINT, signal_handler)

