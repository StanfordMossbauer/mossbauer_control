import sys, os
import pexpect
import time
from os.path import join
import atexit

key_map = {
    'stop': 'S',
    'start': 's',
    'quit': 'q',
    'count': 'n',
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
        if self.process.isalive():
            print('Closing child process.')
            self.send(key_map['stop'])
            self.send(key_map['quit'])
            self.process.terminate()
            self.process.close()
        else:
            print('Child already closed, doing nothing.')
        return

    def checkalive(self):
        """Make sure we haven't closed the program
        """
        assert self.process.isalive(), 'Child process closed!'
        return

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

    def start(self):
        self.send(key_map['start'], 'Readout Rate')
        return

    def stop(self):
        self.send(key_map['stop'], 'Acquisition Stopped for Board 0')
        return

    def timed_acquire(self, time_s):
        """Acquire for fixed time
        TODO: stream readout rate
        """
        self.start()
        time.sleep(time_s)
        self.stop()
        self.update_count()
        return

    def update_count(self):
        """Update the total count
        """
        self.send(key_map['count'], r'[0-9]+')
        assert 'Total Count: ' in str(self.process.before), 'Count failure!'
        self.count = int(self.process.after)
        return


if __name__=='__main__':
    verbose = True
    save = True
    config_file = 'co57_config'

    digi = DPPReadout(config_file, verbose=verbose)
    digi.start()
    time.sleep(100)
    digi.stop()
    digi.update_count()
