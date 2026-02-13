import pyvisa



class SDG1062X:
    def __init__(self, resource_name="USB0::0xF4EC::0x1103::SDG1PA0C900622::INSTR"):
        self.resource_name = resource_name
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(self.resource_name)


    #Basic Waveve form Generation Functions (BSWV)

    def set_frequency(self, channel, frequency):
        self.instrument.write(f"C{channel}:BSWV FRQ,{frequency}")

    def set_phase(self, channel, phase):
        self.instrument.write(f"C{channel}:BSWV PHSE,{phase}")

    def set_amplitude(self, channel, amplitude):
        self.instrument.write(f"C{channel}:BSWV AMP,{amplitude}")

    def set_high_level(self, channel, high_level):
        self.instrument.write(f"C{channel}:BSWV HLEV,{high_level}")

    def set_low_level(self, channel, low_level):
        self.instrument.write(f"C{channel}:BSWV LLEV,{low_level}")  

    def set_waveform(self, channel, waveform = "SQU"):
        #possibilities:SINE, SQUARE, RAMP, PULSE, NOISE, ARB, DC, PRBS, IQ
        self.instrument.write(f"C{channel}:BSWV WVTP,{waveform}")

    def set_offset(self, channel, offset):
        self.instrument.write(f"C{channel}:BSWV OFST,{offset}")

    #Burst Trigger Functions (BTWV)

    def burst_enable(self, channel, mode):
        #possibilities: ON, OFF
        self.instrument.write(f"C{channel}:BTWV STATE {mode}")

    def set_burst_mode(self, channel, mode):
        #possibilities: GATE, NCYC
        self.instrument.write(f"C{channel}:BTWV GATE_NCYC {mode}")

    def set_burst_trigger_source(self, channel, source):
        #possibilities: MAN, EXT, TIM
        self.instrument.write(f"C{channel}:BTWV TRSR {source}")

    def set_burst_trigger_edge(self, channel, edge):
        #possibilities: RISE, FALL
        self.instrument.write(f"C{channel}:BTWV TRED {edge}")

    def set_trigger_delay(self, channel, delay):
        self.instrument.write(f"C{channel}:BTWV DLAY {delay}")

    def set_ncycles(self, channel, count):
        #INF, 1,2...
        self.instrument.write(f"C{channel}:BTWV TIME {count}")

    def close(self):
        self.instrument.close()
        self.rm.close()

    def experiment_setup(self, frequency, delay_ch1, delay_ch2, duty_cycle_ch1=50):
        
        for channel in [1,2]:

            self.set_waveform(channel = channel, waveform="SQU")
            self.burst_enable(channel = channel, mode="ON")
            self.burst_enable(channel = channel, mode="ON")
            self.set_burst_trigger_source(channel = channel, source="EXT")
            self.set_burst_trigger_edge(channel = channel, edge="RISE") 
            

        #Camera trigger
        self.set_frequency(channel = 1, frequency=2*frequency)
        self.set_trigger_delay(channel = 1, delay=delay_ch1)
        self.set_ncycles(channel = 1, count=2)
        self.set_duty_cycle(channel = 1, duty_cycle= duty_cycle_ch1)

        #DAQ input
        self.set_frequency(channel = 2, frequency=frequency)
        self.set_ncycles(channel = 2, count=1)
        self.set_trigger_delay(channel = 2, delay=delay_ch2)

            


        
        self.set_phase(channel = 2, phase=delay_ch2)

       
            


if __name__ == "__main__":

    sdg = SDG1062X()
    sdg.experiment_setup(frequency=1000, absolute_phase_delay=0, releative_phase_delay=90)
