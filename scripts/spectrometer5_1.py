import time 
import os
import numpy as np
import matplotlib.pylab as plt
from tqdm import tqdm
import atexit
import pandas as pd

import mossbauer_control
from mossbauer_control.instruments import CAEN, Agilent, HP33120A, PS2000, BK4060B, HP5335A, Yoctopuce

import paramiko

###TODO: MAKE A SCAN FUNCTION THAT TAKES ARBITRARY WAVEFORM THIS WAY SCANS DONT HAVE TO BE SYMMETRIC.. 
### SO WE WILL HAVE SCAN_SYMMETRIC(v) AND SCAN_SINGLESIDE(v)

def write_results(frequency, results, data_file, print_results=True):
    """Saves results (list of dicts) to file, avoids overwriting"""
    save_kwargs = {}
    if os.path.exists(data_file):
        save_kwargs = dict(mode='a', header=False)
    pd.DataFrame(results).to_csv(data_file, index=False, **save_kwargs)
    #pd.DataFrame(results).drop('hist', axis=1).to_csv(
    #    data_file, index=False, **save_kwargs
    #)
    if print_results:
        print_str = (
            'frequency {freq:.3f}, +/-{vel:.2f} mm/s ' 
            'ch0: {ch0:.2f} Hz ch_1: {ch1:.2f} Hz  ch_2: {ch2:.2f} Hz'
        ).format(
            freq=frequency,
            vel=results[0]['nominal_velocity'],
            ch0=results[0]['count']/results[0]['DAQ_time'],
            ch1=results[1]['count']/results[1]['DAQ_time'],
            ch2=results[0]['unskimmed_count_2x']/results[0]['DAQ_time']/2,
        )
        print(print_str)
    return

class MossbauerSpectrometer:
    def __init__(self):
        """Set up all the instruments for the scan
        HARDCODE WARNING!
        """

        self.scanTime = 48
        self.dutycycle = 0.8

        #self.scanTime = 2
       
        self.picoscope = PS2000()
        self.stage = BK4060B('USB0::62700::60984::575A23113::INSTR')
        self.Yoctopuce = Yoctopuce('METEOMK2-2377A2')

        self.counter1 = HP5335A("GPIB::1::INSTR")
        self.counter2 = HP5335A("GPIB::2::INSTR")
        self.counter3 = HP5335A("GPIB::3::INSTR")

        # Paramiko Connection
        self.hostname = '192.168.31.114'
        self.username = 'root'
        self.password = 'root'
        self.port = 22
        
        self.client = paramiko.client.SSHClient() 
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.hostname,self.port,self.username,self.password)

        # TODO add to setup function
        
        self.temp = 0

        self.insts = [

            self.stage,
            self.counter1,
            self.counter2,
            self.counter3,
            self.picoscope,
        ]

        def exit_function():
            for inst in self.insts:
                inst.close()
        atexit.register(exit_function)

        for inst in self.insts:
            inst.setup_mossbauer_scan()

        return

        #counter1.device.write("AU0")
        #counter2.device.write("AU0")
        self.counter3.device.write("WA1")
        self.counter3.device.write("AU0")
        #self.counter1.set_coupling("DC")
        #self.counter1.set_trigger_level(1.3)

        #self.counter2.set_coupling("DC")
        #self.counter2.set_trigger_level(1.3)

        #self.counter3.set_coupling("AC")
        #self.counter3.set_trigger_level(0.020)


    def disconnect_instruments(self):
            for inst in self.insts:
                inst.close()
                
                
    def dummy_sweep(self):
        """Trigger everything once to sync it all up"""
        print("Trigger everything once to sync it all up")
        for inst in self.insts:
            inst.setup_dummy_sweep()
        self.stage.device.write('*TRG')
        time.sleep(5)
        return

    def zero_velocity_sweep(self):
        """Does a fake sweep to take data with zero velocity"""
        self.stage.assert_output(1, 'OFF')
        results = self.sweep(3*1/self.scanTime) # picoscope buffer is limited...
        results[0]['nominal_velocity'] = 0
        results[1]['nominal_velocity'] = 0
        self.stage.assert_output(1, 'ON')
        #print('velocity +/-{:.2f}'.format(results[0]['nominal_velocity']))
        return results

    def sweep(self, frequency):
        """Run a single sweep (forward + backward)
        frequency: for "ramp" function (velocity = 2*dX*frequency)
        """
        period = 1/frequency
        cycles = int(self.scanTime/period)
        actualscanTime = cycles*period

        try : 
            self.client.connect(self.hostname,self.port,self.username,self.password)
            stdin,stdout,stderr=self.client.exec_command("python3 mossbauer_rp_start.py {}".format(frequency))
            self.client.close()
            #print(stdout.read().decode())
        except : 
            pass 

        
        time.sleep(0.2)
        
        for inst in self.insts:
            inst.setup_sweep(frequency, cycles)    
        time.sleep(0.1) # for setting trigger
        
        self.counter3.device.write("WA1")

        
        
        
        self.counter1.gate_open()
        self.counter2.gate_open()
        self.counter3.gate_open()
        #time.sleep(0.1) # TODO: remove when everything working
        
        self.stage.device.write('C1:BTWV MTRIG')
        
        time.sleep(actualscanTime)

        #self.counter1.gate_close()
        self.counter2.gate_close()
        self.counter3.gate_close()  #counter 2 and 3 behave somehow differently and needs to be closed!

        time.sleep(0.1)

        try: 
            self.client.connect(self.hostname,self.port,self.username,self.password)
            stdin,stdout,stderr=self.client.exec_command("python3 mossbauer_rp_read.py {}".format(frequency))
            self.client.close()
            #print(stdout.read().decode())
        except :
            pass

        
        count1 =self.counter1.read_count2()
        count2 =self.counter2.read_count2()
        count3 =self.counter3.read_count2()
        #print(count1,count2,count3)
        count = [count1,count2,count3]
        self.temp = count
        
        time.sleep(0.5)
    
        self.picoscope.waitReady()
        (data, ovf) = self.picoscope.getDataV('A', returnOverflow=True)
        (gate, ovf) = self.picoscope.getDataV('B', returnOverflow=True)
        
        self.data = data
        self.gate = gate

        fit_vels, fit_errs, fit_msr = mossbauer_control.fit_picoscope_data(
            self.stage.Xmax - self.stage.Xmin, 
            self.stage.Vmax - self.stage.Vmin,
            frequency, 
            data, 
            gate, 
            [self.picoscope.sampleInterval,self.picoscope.noSamples],
            plot = False
        )

        print(fit_vels)

        #fit_vels, fit_errs, fit_msr = np.array([0,0,0])
        

        multiplier = {0: -1, 1: 1}  # determines neg and pos
        results = []
        #count = [self.counter1.read_count(),self.counter2.read_count(),self.counter3.read_count()]
        for ch in (0,1):
            results.append(dict(
                    count=count[ch],
                    unskimmed_count_2x = count[2],
                    DAQ_time=(actualscanTime/2*self.dutycycle),
                    nominal_velocity=(
                        2 * (self.stage.Xmax - self.stage.Xmin)
                        * frequency
                        * multiplier[ch]
                    ),
                    frequency=frequency,
                    fit_velocity=fit_vels[ch],
                    fit_err=fit_errs[ch],
                    fit_msr=fit_msr[ch],
                    temperature = self.Yoctopuce.temperature.get_currentValue(),
                    pressure = self.Yoctopuce.pressure.get_currentValue(),
                    humidity = self.Yoctopuce.humidity.get_currentValue(),
                    time=time.time()
            ))
            
        return results

    def scan(self, frequencies, repetitions, data_file='test.dat'):
    
    #Perform constant-velocity mossbauer scan frequencies: list of frequencies for triangle wave stage motion
        
        #self.dummy_sweep() only for v3
        
        for j in range(repetitions):
            for frequency in frequencies:
                if frequency==0:
                    results = self.zero_velocity_sweep()
                else:
                    results = self.sweep(frequency)
                write_results(frequency, results, data_file)
        return

        

if __name__ == "__main__":
    
    repetitions = 1000000
    #repetitions = 1

    frequencies = np.linspace(0, 1.5, 25)[1:]  # standard 25pts
    #frequencies = np.linspace(0, 2., 33)[1:]
    #frequencies = np.array([0.14, 0.16])
    #frequencies = np.array([0.16])

    #frequencies = np.array([0.365, 0.135])  # manually converted (FeCy 2pts, v=0.232, 0.086 mm/s)
    #-0.040, -0.25  f = v/(2*xmax), xmax = 318e-3 ->round(0.25/(2*318e-3)*100)/100, round(0.04/(2*318e-3)*100)/100
    #frequencies = np.array([0.39, 0.06])
    

    directory = "/home/mossbauer/Data/mossbauer_data/{}_scan/".format(time.strftime("%Y%m%d"))
    data_file = directory + 'Fe20um_1BeBlank_4steps_1in2.dat'
    if not os.path.isdir(directory):
        os.mkdir(directory)

    protect_overwrite = False
    if protect_overwrite:
        if os.path.isfile(data_file): 
            print('filename exists choose another one!') 
            sys.exit()

    scan = MossbauerSpectrometer()
    scan.scanTime = 48
    scan.dutycycle = 0.7  #this is not a setting, it must be controlled on the redpitaya. here just for knowledge
    scan.scan(frequencies, repetitions, data_file)
    #scan.scanTime = 2
    #result = scan.sweep(1)
