import time
import os
import sys
import numpy as np
import matplotlib.pylab as plt
from tqdm import tqdm
import atexit
import pandas as pd
from mossbauer_control.utils import fit_residuals

from mossbauer_control.instruments import CAEN, Agilent, HP33120A, PS2000, BK4060B

def fit_picoscope_data(Xrange, Vrange, frequency, data, gate, actualSamplingInfo, plot = False, save = False):

    fs = 1/actualSamplingInfo[0]
    period = actualSamplingInfo[0]*actualSamplingInfo[1]
    cycles = int(period*frequency)

    clip = int(cycles/frequency*fs)//cycles*cycles

    data = data[:clip].reshape(cycles,-1).mean(axis = 0)
    gate = gate[:clip].reshape(cycles,-1).mean(axis = 0)

    dataP = data[:len(data)//2]
    maskP = gate[:len(data)//2] > 5
    dataN = data[len(data)//2:]
    maskN = gate[len(data)//2:] > 5

    dataN = dataN[maskN]
    dataP = dataP[maskP]

    def slope(p,x):
        a,b = p
        return a+b*x

    p0 = [5,1]
    xdataP = np.arange(len(dataP))/fs
    xdataN = np.arange(len(dataN))/fs

    try:
       pP, dpP, msrP = fit_residuals(slope, xdataP, dataP, p0, fullout=False)
       pN, dpN, msrN = fit_residuals(slope, xdataN, dataN, p0, fullout=False)
        
    except Exception as e:
        print(e)
        pP, dpP, msrP = np.zeros(3)
        pN, dpN, msrN = np.zeros(3)

    if plot:
        plt.figure()
        plt.plot(xdataP, dataP)
        plt.plot(xdataN, dataN)
        plt.plot(xdataP, slope(pP, xdataP))
        plt.plot(xdataP, slope(pN, xdataN))
        plt.show()

    if save:
        file = open('psdata_ramp.dat', 'w')
        data.tofile(file)
        file = open('psdata_gate.dat', 'w')
        gate.tofile(file)

    fit_vels = [pP[1]*Xrange/Vrange, pN[1]*Xrange/Vrange]
    fit_errs = [dpP[1]*Xrange/Vrange, dpN[1]*Xrange/Vrange]
    fit_msr = [msrP*Xrange/Vrange, msrN*Xrange/Vrange]

    return fit_vels, fit_errs, fit_msr

def write_results(frequency, results, data_file, print_results=True):
    save_kwargs = {}
    if os.path.exists(data_file):
        save_kwargs = dict(mode='a', header=False)
    pd.DataFrame(results).to_csv(data_file, index=False, **save_kwargs)
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

class MossbauerScan:
    def __init__(self):

        self.Xmax = 318e-3
        self.Xmin = 0e-3

        self.scanTime = 48

        self.clock = Agilent("GPIB::14::INSTR")
        self.skim = HP33120A("GPIB::15::INSTR")
        self.stage = BK4060B('USB0::62700::60984::575A23113::INSTR')
        self.caen = CAEN("/home/mossbauer/mossbauer_control/caen_configs/co57_config_2ch")

        self.ps = PS2000()
        # TODO add to setup function
        self.ps.setChannel(channel='A', coupling='DC', VRange=10, VOffset=0.0, enabled=True)
        self.ps.setChannel(channel='B', coupling='DC', VRange=10, VOffset=0.0, enabled=True)
        self.actualSamplingInfo = self.ps.setSamplingInterval(5e-3,40)

        self.insts = [
            self.clock,
            self.skim,
            self.stage,
            self.caen
        ]

        def exit_function():
            for inst in self.insts:
                inst.close()
        atexit.register(exit_function)

        for inst in self.insts:
            inst.setup_mossbauer_scan()

        return

    def dummy_sweep(self):
        print('dummy scan')
        #### Dummy Sweep ####
        for inst in self.insts:
            inst.setup_dummy_sweep()
        self.clock.device.write('*TRG')
        time.sleep(5)
        #####################
        print('dummy scan done')
        return

    def zero_velocity_sweep(self):
        # I'm sure we could combine with sweep()
        self.stage.assert_output(1, 'OFF')
        results = self.sweep(3*1/self.scanTime) # picoscope buffer is limited...
        results[0]['nominal_velocity'] = 0
        results[1]['nominal_velocity'] = 0
        self.stage.assert_output(1, 'ON')
        return results

    def sweep(self, frequency):
        period = 1/frequency
        cycles = int(self.scanTime/period)
        actualscanTime = cycles*period

        for inst in self.insts:
            inst.setup_sweep(frequency, cycles)

        self.ps.setSimpleTrigger(trigSrc="B", threshold_V=1.0, direction="Rising", delay=0, enabled=True, timeout_ms=int(5e3))
        self.ps.runBlock()
        time.sleep(0.1)

        # beware of command-induced delays!
        self.caen.start() 
        time.sleep(1)  # TODO: remove when everything working
        self.clock.device.write('*TRG')

        print('sleep for %d secs' % actualscanTime)
        time.sleep(actualscanTime)
        time.sleep(1)  # TODO: remove when everything working
        self.caen.stop()

        self.ps.waitReady()
        (data, ovf) = self.ps.getDataV('A', returnOverflow=True)
        (gate, ovf) = self.ps.getDataV('B', returnOverflow=True)

        fit_vels, fit_errs, fit_msr = fit_picoscope_data(
            self.Xmax-self.Xmin, 
            self.stage.Vmax-self.stage.Vmin,
            frequency, 
            data, 
            gate, 
            self.actualSamplingInfo, 
            plot = False,
            save = False
            )

        self.caen.update_count()
        multiplier = {0: 1, 1: -1}  # determines neg and pos
        results = [
            dict(
                count=(self.caen.count[ch]),
                DAQ_time=(actualscanTime/2*self.skim.dutycycle/100),
                nominal_velocity=(2*(self.Xmax-self.Xmin)*frequency*multiplier[ch]),
                fit_velocity=fit_vels[ch],
                fit_err=fit_errs[ch],
                fit_msr=fit_msr[ch],
            )
            for ch in (0, 1)
        ]
        self.caen.send('r')
        return results

    def scan(self, frequencies, repetitions, data_file='test.dat'):
        self.dummy_sweep()
        for j in range(repetitions):
            for frequency in frequencies:
                if frequency==0:
                    results = self.zero_velocity_sweep()
                else:
                    results = self.sweep(frequency)
                write_results(frequency, results, data_file)
        return


if __name__=='__main__':
    scan = MossbauerScan()
    frequencies = np.linspace(0, 1.5, 25)
    repetitions = 1000

    directory = "/home/mossbauer/Data/{}_scan/".format(time.strftime("%Y%m%d"))
    data_file = directory + 'FeCye_0.9_mms_25steps_0.6-17in.dat'
    #data_file = directory + 'test2'
    if not os.path.isdir(directory):
        os.mkdir(directory)

    protect_overwrite = True
    if protect_overwrite:
        ## avoids overwriting
        if os.path.isfile(data_file): 
            print('filename exists choose another one!') 
            sys.exit()

    scan.scan(frequencies, repetitions, data_file)
