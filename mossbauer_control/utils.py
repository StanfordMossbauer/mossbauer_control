"""
Eventually we should put plotting functions etc here
"""

import logging
# Plot the four (two analog, two digital) traces
# output by the c-demo code. For configuring DPP settings.

import numpy as np
import matplotlib.pyplot as plt

def plot_caen_traces():
    fn_map = {
        'Input': 'Waveform_0_0_1.txt',
        'TrapezoidReduced': 'Waveform_0_0_2.txt',
        'Peaking': 'DWaveform_0_0_1.txt',
        'Trigger': 'DWaveform_0_0_2.txt',
    }

    arr_map = {}
    fig2, ax2 = plt.subplots(2, 2)
    fig, ax = plt.subplots(1)
    ax3 = ax.twinx()
    for i, (key, val) in enumerate(fn_map.items()):
        with open(val) as f:
            arr_map[key] = np.array([int(v) for v in f.readlines()])
        ax2[int(i/2)][i % 2].plot(arr_map[key], label=key)
        ax2[int(i/2)][i % 2].set_title(key)
        if i<2:
            ax.plot(arr_map[key], label=key)
        else:
            ax3.plot(arr_map[key], label=key)
    plt.legend(loc='best')
    fig2.tight_layout()
    plt.show()
    return

class StreamToLogger(object):
    """Fake file-like stream object that redirects writes to a logger instance.

    from https://stackoverflow.com/questions/19425736/how-to-redirect-stdout-and-stderr-to-logger-in-python
    """
    def __init__(self, logger, level):
       self.logger = logger
       self.level = level
       self.linebuf = ''
       return

    def write(self, buf):
       for line in buf.rstrip().splitlines():
          self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass
