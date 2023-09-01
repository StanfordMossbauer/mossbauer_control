import time
import os
import numpy as np
import matplotlib.pylab as plt
from tqdm import tqdm
import atexit
import pandas as pd

import mossbauer_control
from mossbauer_control.instruments import CAEN, Agilent, HP33120A, PS2000, BK4060B

def write_results(frequency, results, data_file, print_results=True):
    """Saves results (list of dicts) to file, avoids overwriting"""
    save_kwargs = {}
    if os.path.exists(data_file):
        save_kwargs = dict(mode='a', header=False)
    pd.DataFrame(results).drop('hist', axis=1).to_csv(
        data_file, index=False, **save_kwargs
    )
    if print_results:
        print_str = (
            'frequency {freq:.3f}, +/-{vel:.2f} mm/s ' 
            'ch0: {ch0:.2f} Hz ch_1: {ch1:.2f} Hz ratio: {rat:.2f}'
        ).format(
            freq=frequency,
            vel=results[0]['nominal_velocity'],
            ch0=results[0]['count']/results[0]['DAQ_time'],
            ch1=results[1]['count']/results[1]['DAQ_time'],
            rat=results[1]['count']/results[0]['count'],
        )
        print(print_str)
    return

class MossbauerSpectrometer:
    def __init__(self):
        """Set up all the instruments for the scan
        HARDCODE WARNING!
        """

        self.scanTime = 48

        self.skim_lower = 644
        self.skim_upper = 1106

        # something wrong between ch 0-1-2
        self.skim_lower = 600
        self.skim_upper = 1000

        self.clock = Agilent("GPIB::14::INSTR")
        self.skim = HP33120A("GPIB::15::INSTR")
        self.stage = BK4060B('USB0::62700::60984::575A23113::INSTR')
        self.caen = CAEN("/home/mossbauer/mossbauer_control/caen_configs/co57_config_2ch")

        self.picoscope = PS2000()

        # TODO add to setup function

        self.insts = [
            self.clock,
            self.skim,
            self.stage,
            self.caen,
            self.picoscope,
        ]

        def exit_function():
            for inst in self.insts:
                inst.close()
        atexit.register(exit_function)

        for inst in self.insts:
            inst.setup_mossbauer_scan()

        return

    def dummy_sweep(self):
        """Trigger everything once to sync it all up"""
        print('dummy sweep')
        for inst in self.insts:
            inst.setup_dummy_sweep()
        self.clock.device.write('*TRG')
        time.sleep(5)
        print('dummy sweep done')
        return

    def zero_velocity_sweep(self):
        """Does a fake sweep to take data with zero velocity"""
        self.stage.assert_output(1, 'OFF')
        results = self.sweep(3*1/self.scanTime) # picoscope buffer is limited...
        results[0]['nominal_velocity'] = 0
        results[1]['nominal_velocity'] = 0
        self.stage.assert_output(1, 'ON')
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

        # beware of command-induced delays!
        self.caen.start() 
        time.sleep(1)  # TODO: remove when everything working
        self.clock.device.write('*TRG')

        print('sleep for %d secs' % actualscanTime)
        time.sleep(actualscanTime)
        time.sleep(1)  # TODO: remove when everything working
        self.caen.stop()

        self.picoscope.waitReady()
        (data, ovf) = self.picoscope.getDataV('A', returnOverflow=True)
        (gate, ovf) = self.picoscope.getDataV('B', returnOverflow=True)

        fit_vels, fit_errs, fit_msr = mossbauer_control.fit_picoscope_data(
            self.stage.Xmax - self.stage.Xmin, 
            self.stage.Vmax - self.stage.Vmin,
            frequency, 
            data, 
            gate, 
            self.picoscope.actualSamplingInfo, 
        )

        self.caen.update_count()
        multiplier = {0: 1, 1: -1}  # determines neg and pos
        results = []
        for ch in (0, 1):
            hist = self.caen.histogram(ch)
            count = hist[self.skim_lower:self.skim_upper].sum()
            results.append(dict(
                    count=count,
                    unskimmed_count=self.caen.count[ch],
                    DAQ_time=(actualscanTime/2*self.skim.dutycycle/100),
                    nominal_velocity=(
                        2 * (self.stage.Xmax - self.stage.Xmin)
                        * frequency
                        * multiplier[ch]
                    ),
                    frequency=frequency,
                    fit_velocity=fit_vels[ch],
                    fit_err=fit_errs[ch],
                    fit_msr=fit_msr[ch],
                    time=time.time(),
                    hist=hist,
            ))
        # clear the data from caen memory
        self.caen.send('r')
        return results

    def scan(self, frequencies, repetitions, data_file='test.dat'):
        """Perform constant-velocity mossbauer scan

        frequencies: list of frequencies for triangle wave stage motion
        """
        self.histogram = [
            {f: np.zeros(16384) for f in frequencies} for ch in (0, 1)
        ]
        self.avg_norm = {f: 0 for f in frequencies}
        self.dummy_sweep()
        for j in range(repetitions):
            for frequency in frequencies:
                if frequency==0:
                    results = self.zero_velocity_sweep()
                else:
                    results = self.sweep(frequency)
                write_results(frequency, results, data_file)
                for ch in (0, 1):
                    hist = results[ch]['hist']
                    self.histogram[ch][frequency] = (
                        (self.histogram[ch][frequency]*self.avg_norm[frequency])
                        + hist
                    ) / (self.avg_norm[frequency] + 1)
                    #print(self.histogram[ch][frequency])
                    hist_fname = data_file.split('.dat')[0] + f'_avghist_{frequency}Hz_Ch{ch}.dat'
                    #print(ch, frequency)
                    #print(self.histogram[ch][frequency])
                    np.savetxt(hist_fname, self.histogram[ch][frequency], fmt='%s')
                self.avg_norm[frequency] += 1
        return
