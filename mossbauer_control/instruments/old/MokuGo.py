"""
This was taken from Gautam's old code and was specifically for controlling
the stepper through the MokuGo. It is no longer used in the current setup.
"""

from moku.instruments import WaveformGenerator, Oscilloscope

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
        print('trying')
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
