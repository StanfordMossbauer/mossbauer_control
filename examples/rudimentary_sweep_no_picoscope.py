import time
import os
import sys
import numpy as np
from mossbauer_control.instruments import CAEN, Agilent, HP33120A, PS4000, BK4060B
#from picoscope import ps4000
import mossbauer_control as m
import matplotlib.pylab as plt
from tqdm import tqdm
import atexit

directory = "/home/mossbauer/Data/{}_scan/".format(time.strftime("%Y%m%d"))
#data_file = directory + 'Fe0004_0.5_mms_0.01_mms_19in.dat'
#data_file = directory + 'BeBlankUnpolished_1_mms_0.05_mms_19in.dat'
#data_file = directory + 'Fe0004_1_mms_0.05_mms_19in.dat'
#data_file = directory + 'Fe0004_1_mms_0.05_mms_19in_cardboard.dat'
data_file = directory + 'FeCy_0.6_mms_9steps_0.6-17in.dat'
data_file = directory + 'Fe0004_0.9_mms_13steps_0.6-17in.dat'
#data_file = directory + 'Fe0004_0.6_mms_outersteps_0.6-17in.dat'

#protect_overwrite = False
protect_overwrite = True


Vmax = 10
Vmin = 0
Xmax = 318e-3
Xmin = 0e-3



frequencies = np.linspace(0, 1, 9)#[np.linspace(0,0.5,51)[21]]#np.ones(5)# np.linspace(0, 150, 4)#
frequencies = np.linspace(0, 1.5, 13)#[-4:]
#scanTime = 3/frequencies[1]
scanTime = 24
if scanTime<(1/frequencies[1:].min()): print("Careful too shot time for lower frequency")

#for testing
#frequencies = np.ones(100)
#frequencies = np.zeros(100)
#scanTime = 10


vellist = frequencies*(2*(Xmax-Xmin))
repetitions = 1000

def lin(p,x):
    a,b= p
    return a+b*x


if not os.path.isdir(directory): os.mkdir(directory)

if protect_overwrite:
    ## avoids overwriting
    if os.path.isfile(data_file): 
        print('filename exists choose another one!') 
        sys.exit()

with open(data_file, 'w') as f:
        f.write('nom_vel\tvel\tmsr\tcount\tseconds\n')



clock = Agilent("GPIB::14::INSTR")
skim = HP33120A("GPIB::15::INSTR")
stage = BK4060B('USB0::62700::60984::575A23113::INSTR')
caen = CAEN("/home/mossbauer/mossbauer_control/caen_configs/co57_config_2ch")

insts = [clock, skim, stage, caen]

def exit_function():
    for inst in insts:
        inst.close()
atexit.register(exit_function)

for inst in insts:
    inst.setup_mossbauer_scan()

scanTime = 24

prev_count = np.zeros(8, dtype=int)


print('dummy scan')
#### Dummy Sweep ####
for inst in insts:
    inst.setup_dummy_sweep()
clock.device.write('*TRG')
time.sleep(5)
#####################
print('dummy scan done')


def zero_velocity_sweep():
    # I'm sure we could combine with sweep()
    stage.assert_output(1, 'OFF')
    results = sweep(1/scanTime)  # TODO
    stage.assert_output(1, 'ON')
    return results

def sweep(frequency):
    period = 1/frequency
    cycles = int(scanTime/period)
    actualscanTime = cycles*period

    for inst in insts:
        inst.setup_sweep(frequency, cycles)

    # beware of command-induced delays!
    caen.start() 
    time.sleep(1)  # TODO: remove when everything working
    clock.device.write('*TRG')

    print('sleep for %d secs' % actualscanTime)
    time.sleep(actualscanTime)
    time.sleep(1)  # TODO: remove when everything working
    caen.stop()
    caen.update_count()
    multiplier = {0: 1, 1: -1}  # determines neg and pos
    # TODO add fitting / actual velocity
    results = [
        dict(
            count=caen.count[ch] - prev_count[ch],
            DAQ_time=actualscanTime/2*skim.dutypercent/100,
            nominal_velocity=2*(Xmax-Xmin)*frequency*multiplier[ch],
        )
        for ch in (0, 1)
    ]
    prev_count = caen.count
    return results

def write_results(frequency, results, data_file, print_results=True):
    save_kwargs = {}
    if os.path.exists(data_file):
        save_kwargs = dict(mode='a', index=False, header=False)
    pd.DataFrame(results).to_csv(data_file, **save_kwargs)
    if print_results:
        print_str = """
        full scans: {this}/{total}, frequency {freq:.3f}, +/-{vel:.2f} mm/s ch0: {ch0:.2f} Hz ch_1: {ch1:.2f} Hz ratio: {rat:.2f}
        """.format(
            this=j,
            total=repetitions,
            freq=frequency,
            vel=results[0]['nominal_velocity'],
            ch0=results[0]['count']/results[0]['DAQ_time'],
            ch1=results[1]['count']/results[1]['DAQ_time'],
            rat=results[1]['count']/results[0]['count'],
        )
        print(print_str)
    return

for j in range(repetitions):
    for frequency in frequencies:
        if frequency==0:
            results = zero_velocity_sweep()
        else:
            results = sweep(frequency)
        write_results(frequency, results, data_file)
