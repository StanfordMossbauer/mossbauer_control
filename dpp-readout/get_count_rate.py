from DPPReadout import DPPReadout, key_map
import sys, os
from os.path import join
import time

daqdir = '/home/joeyh/daq/dpp-pha/dpp-readout'
datadir = '/home/joeyh/analysis/'
config_file = 'unamplified_config'

start_time = time.time()
try:
    time_s = int(sys.argv[1])
    velocity = float(sys.argv[2])
    name = sys.argv[3]
except IndexError:
    print('Usage: python get_count_rate.py <time (seconds)> <velocity (mm/s)> <name (e.g. YYYYMMDD_i)>')
    sys.exit()

data_file = join(datadir, name + '.dat')
if not os.path.exists(data_file):
    with open(data_file, 'w') as f:
        f.write('vel\tcount\tseconds\tstart-time\t\tstop-time\n')

digitizer = DPPReadout(join(daqdir, config_file))
digitizer.timed_acquire(time_s)
count = digitizer.count
stop_time = time.time()
print(f'Total Count: {count}')
with open(data_file, 'a') as f:
    f.write(f'{velocity}\t{count}\t{time_s}\t{start_time}\t{stop_time}\n')
