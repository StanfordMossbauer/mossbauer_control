import sys, os
import pexpect
import time
from os.path import join
import atexit

import numpy as np

key_map = {
    'stop': 'S',
    'start': 's',
    'quit': 'q',
}

class DPPReadout:
    """Class to wrap dpp-readout and interface with digitizer.
    Code was adapted from the script caen_handler.py, which Chas
    wrote to interact with the wavedump software.
    """
    def __init__(self, config_file='', verbose=False):
        self.verbose = verbose
        self.process = pexpect.spawn(f'dpp-readout {config_file}')
        self.expect('Save waveforms to file\r\n\r\n\r\n')
        atexit.register(self.close)  # close self if python process dies
        self.start_time = time.time()
        return

    def close(self):
        """Stop current acquisition, quit the program, end the process
        """
        print('Closing child process.')
        self.send(key_map['stop'])
        self.send(key_map['quit'])
        self.process.terminate()
        self.process.close()
        return

    def checkalive(self):
        """Make sure we haven't closed the program
        """
        assert self.process.isalive(), 'Child process closed!'

    def expect(self, exp):
        """Expect a specified output string, close if not, print if asked
        """
        try:
            self.process.expect(exp, timeout=1)
        except:
            print("expect() failed!")
            self.close()
        if self.verbose:
            print(self.process.before.decode('ascii'), end='')
            print(self.process.after.decode('ascii'), end='')
        return

    def send(self, line, expect_string=None):
        """Send arbitrary line to dpp-readout, optionally expecting output
        """
        self.checkalive()
        self.process.send(line)
        if expect_string is not None:
            self.expect(expect_string)
        return


if __name__=='__main__':
    verbose = True
    save = True
    config_file = 'unamplified_config'
    base_path = '/home/joeyh/local_data/'
    meas_name = 'test'
    save_path = join(base_path, meas_name)

    base_filename = 'am241'

    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    digi = DPPReadout(config_file, verbose=True)
