import time
import os
import numpy as np
import matplotlib.pylab as plt
from tqdm import tqdm
import atexit
import pandas as pd

import mossbauer_control
from mossbauer_control.instruments import CAEN, Agilent, HP33120A, PS2000, BK4060B, HP5335A


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
        #self.scanTime = 2
       
        self.clock = Agilent("GPIB::14::INSTR")
        self.skim = HP33120A("GPIB::15::INSTR")
        self.stage = BK4060B('USB0::62700::60984::575A23113::INSTR')
        self.counter1 = HP5335A("GPIB::1::INSTR")
        self.counter2 = HP5335A("GPIB::2::INSTR")
        self.counter3 = HP5335A("GPIB::3::INSTR")
        
        #self.picoscope = PS2000()

        # TODO add to setup function
        
        self.temp = 0

        self.insts = [
            self.clock,
            self.skim,
            self.stage,
            self.counter1,
            self.counter2,
            self.counter3,
         #   self.picoscope,
        ]

        def exit_function():
            for inst in self.insts:
                inst.close()
        atexit.register(exit_function)

        for inst in self.insts:
            inst.setup_mossbauer_scan()

        self.counter3.device.write("WA1") #counter 3 behaves differently!

        return


    def disconnect_instruments(self):
            for inst in self.insts:
                inst.close()
                
                
    def dummy_sweep(self):
        """Trigger everything once to sync it all up"""
        print("Trigger everything once to sync it all up")
        #for inst in self.insts:
        #    inst.setup_dummy_sweep()
        self.clock.device.write('*TRG')
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

        for inst in self.insts:
            inst.setup_sweep(frequency, cycles)
            
        #self.picoscope.setSamplingInterval(5e-3,min(self.scanTime,40))
        #si = self.picoscope.setSamplingInterval(5e-3,1)
        #print(si)
        #trigger = self.picoscope.setSimpleTrigger(trigSrc="B",threshold_V= 1.0,direction="Rising",delay=0,enabled=True,timeout_ms=int(5e3))   
        time.sleep(0.1) # for setting trigger
        #rint('setting up trigger',trigger)
        # beware of command-induced delays!
        #self.caen.start() 
        
        
        self.counter1.gate_open()
        self.counter2.gate_open()
        self.counter3.gate_open()
        time.sleep(0.1) # TODO: remove when everything working
        
        
        #scan.picoscope.runBlock
        
        self.clock.device.write('*TRG')
        #print("triggered")
        #scan.picoscope.waitReady()
        #print('picoscope data ready')
        #print('sleep for %d secs' % actualscanTime)
        time.sleep(actualscanTime)
        time.sleep(1)  # TODO: remove when everything working
        #self.caen.stop()
        #self.counter1.gate_close()
        #self.counter2.gate_close()
        self.counter3.gate_close()  #counter 3 behaves somehow differently and needs to be closed!
        count1 =self.counter1.read_count2()
        count2 =self.counter2.read_count2()
        #time.sleep(0.1)
        count3 =self.counter3.read_count2()
        count = [count1,count2,count3]
        self.temp = count
        #self.caen.update_count()
        time.sleep(0.1)
    #    return
    
    #    self.picoscope.waitReady()
    #    (data, ovf) = self.picoscope.getDataV('A', returnOverflow=True)
    #    (gate, ovf) = self.picoscope.getDataV('B', returnOverflow=True)
        
    #    self.temp = data 
        
    #    fit_vels, fit_errs, fit_msr = mossbauer_control.fit_picoscope_data(
    #        self.stage.Xmax - self.stage.Xmin, 
    #        self.stage.Vmax - self.stage.Vmin,
    #        frequency, 
    #        data, 
    #        gate, 
    #        self.picoscope.actualSamplingInfo, 
    #    ) 
        #fit_vels, fit_errs, fit_msr = np.array([0,0,0])
        
        
        multiplier = {0: 1, 1: -1}  # determines neg and pos
        results = []
        #count = [self.counter1.read_count(),self.counter2.read_count(),self.counter3.read_count()]
        for ch in (0,1):
            results.append(dict(
                    count=count[ch],
                    unskimmed_count_2x = count[2],
                    #unskimmed_count=self.caen.count[ch],
                    DAQ_time=(actualscanTime/2*self.skim.dutycycle/100),
                    nominal_velocity=(
                        2 * (self.stage.Xmax - self.stage.Xmin)
                        * frequency
                        * multiplier[ch]
                    ),
                    frequency=frequency,
         #           fit_velocity=fit_vels[ch],
         #           fit_err=fit_errs[ch],
         #           fit_msr=fit_msr[ch],
                    time=time.time(),
                    #total=count[3],
            ))
            
        self.temp = results
        #print('velocity +/-{:.2f}'.format(results[0]['nominal_velocity']))

        # clear the data from caen memory
        #self.caen.send('r')
        #self.counter1.reset()
        #self.counter2.reset()
        #self.counter3.reset()
        return results

    def scan(self, frequencies, repetitions, data_file='test.dat'):
    
    #Perform constant-velocity mossbauer scan frequencies: list of frequencies for triangle wave stage motion
        
        self.dummy_sweep()
        
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
    frequencies = np.linspace(0, 1.5, 25)  # standard 25pts
    frequencies = np.linspace(0, 2., 33)
    frequencies = np.array([0.14, 0.16])
    #frequencies = np.array([0.365, 0.135])  # manually converted (FeCy 2pts, v=0.232, 0.086 mm/s)
    #-0.040, -0.25  f = v/(2*xmax), xmax = 318e-3 ->round(0.25/(2*318e-3)*100)/100, round(0.04/(2*318e-3)*100)/100
    #frequencies = np.array([0.39, 0.06])
    

    directory = "/home/mossbauer/Data/mossbauer_data/{}_scan/".format(time.strftime("%Y%m%d"))
    data_file = directory + 'Fe20um_Al200um_4steps_2in.dat'
    if not os.path.isdir(directory):
        os.mkdir(directory)

    protect_overwrite = False
    if protect_overwrite:
        if os.path.isfile(data_file): 
            print('filename exists choose another one!') 
            sys.exit()

    scan = MossbauerSpectrometer()
    scan.scanTime = 48
    scan.scan(frequencies, repetitions, data_file)
    #scan.scanTime = 2
    #result = scan.sweep(1)
    