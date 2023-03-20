import pyvisa
from time import sleep

#################
## FUNC GEN CONFIG #
DUTY = 50           # Duty cycle
MAX_FREQ = 500e3    # Don't pulse faster than this. Controller technically can handle up to 1MHz.
LOAD = 'HZ'         # Hi Z load by default.
WAVEFORM = 'PULSE'  # Type of waveform
AMP = 5             # Amplitude of pulse
OFFSET = 2.5        # Makes a TTL like signal with the above amp

#################

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
