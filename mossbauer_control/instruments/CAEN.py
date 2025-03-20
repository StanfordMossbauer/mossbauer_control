import sys, os
import pexpect
import time
from os.path import join
import termplotlib as tpl
import numpy as np
import atexit
import re

from .base import *

key_map = {
    'stop': 'S',
    'start': 's',
    'quit': 'q',
    'count': 'n',
    'histogram': 'h',
    'restart': 'r',
}

class CAEN(MossbauerInstrument):
    """Class to wrap dpp-readout and interface with digitizer.
    Code was adapted from the script caen_handler.py, which Chas
    wrote to interact with the wavedump software.
    """
    def __init__(self, config_file='', verbose=False):
        
        self.config_file = config_file
        self.verbose = verbose
        self.nchannels = 8
        self.run()

        return
    
    def run(self):
        self.count = np.zeros(self.nchannels, dtype=int)
        self.process = pexpect.spawn(f'dpp-readout {self.config_file}')
        self.expect('Save waveforms to file\r\n\r\n\r\n')
        atexit.register(self.close)  # close self if python process dies
        self.start_time = time.time()
        
    def close(self):
        """Stop current acquisition, quit the program, end the process"""
        if self.process.isalive():
            print('Closing child process.')
            self.send(key_map['stop'])
            self.send(key_map['quit'])
            self.process.terminate()
            self.process.close()
        else:
            print('Child already closed, doing nothing.')
        return

    def reset(self):
        self.close()
        self.run()

        
    def checkalive(self):
        """Make sure we haven't closed the program"""
        assert self.process.isalive(), 'Child process closed!'
        return

    def expect(self, exp):
        """Expect a specified output string, close if not, print if asked"""
        try:
            self.process.expect(exp, timeout=1)
        except:
            print("expect() failed!")
            print(self.process.before.decode('ascii'), end='')
            print(self.process.after.decode('ascii'), end='')
            self.close()
        if self.verbose:
            print(self.process.before.decode('ascii'), end='')
            print(self.process.after.decode('ascii'), end='')
        return

    def send(self, line, expect_string=None):
        """Send arbitrary line to dpp-readout, optionally expecting output"""
        self.checkalive()
        self.process.send(line)
        if expect_string is not None:
            self.expect(expect_string)
        return

    def start(self):
        # TODO: add expect string
        self.send(key_map['start'])
        return

    def stop(self):
        self.send(key_map['stop'], 'Acquisition Stopped for Board 0')
        return

    def timed_acquire(self, time_s):
        """Acquire for fixed time
        TODO: stream readout rate
        """
        self.start()
        self.send('r')
        time.sleep(time_s)
        self.stop()
        self.update_count()
        return

    def update_count(self):
        """Update the total count"""
        self.send(key_map['count'])
        pattern = 'Channel ([0-9]) Count: ([0-9]*)'
        repattern = re.compile(pattern)
        for i in range(self.nchannels):
            self.send('%d' % i, pattern)
            line = self.process.after
            m = repattern.search(str(line))
            assert int(m.group(1))==i, line
            self.count[i] = int(m.group(2))
        return

    def histogram(self, channel=0, savefile=None, skim_lower=0, skim_upper=None):
        "creates the histogram as Histo_0_0.txt, reads prints it in terminal and saves it with new name"
        self.send('h')
        time.sleep(0.1) # wait for file to update!
        file0 = (f'Histo_0_{channel}.txt')
        hist = np.loadtxt(file0)
        if savefile is not None:
            np.savetxt(savefile, hist, fmt='%s')
        return hist[skim_lower:skim_upper]
        
        

if __name__=='__main__':
    verbose = False
    config_file = 'caen_configs/co57_config_2ch'
    integration_time = 1000
    channel = 2
    digi = CAEN(config_file, verbose=verbose)
    digi.timed_acquire(integration_time)
    rate = digi.count[channel]/integration_time
    print('%.1f +/- %.2f' % (rate, rate*1/np.sqrt(digi.count[channel])))
