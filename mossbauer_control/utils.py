


"""
Eventually we should put plotting functions etc here
"""

import logging
# Plot the four (two analog, two digital) traces
# output by the c-demo code. For configuring DPP settings.

import numpy as np
import matplotlib.pyplot as plt


import time
from numpy import *

from scipy.interpolate import  splrep, splev
from scipy.optimize import leastsq
from scipy.optimize import curve_fit
from scipy.optimize import minimize

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


def fit_residuals(fun, x, y, p0, xmin=None, xmax=None, fullout=True):
    if not xmin:
        xmin = min(x)
    if not xmax:
        xmax = max(x)
    cond = greater_equal(x, xmin) * less_equal(x, xmax)
    x = compress(cond, x)
    y = compress(cond, y)

    def cost(p, x, y):
        return y - fun(p, x)

    [p, cov_p, infodict, ier, m] = leastsq(cost, p0, args=(x, y), full_output=1)
    res = y - fun(p, x)
    sig = res.std()
    dp = sqrt(diag(cov_p)) * sig

    if fullout:
        npar=len(p0)
        print()
        print()
        print("Mean squared residual: %.3e" % (res**2).mean())
        print()
        print( "Covariance Matrix:")
        print()
        print( 5*" ",end='')
        for i in  range(npar):
            print(("p["+str(i)+"]").rjust(6),end='')
        print(  )

        for i in range(npar):
            print(("p["+str(i)+"]").rjust(5),end='')    
            for j in range(0,i+1): #per i=0 ritorna [0] invece di []=range(0)
                print(("%.2f" % (cov_p[i,j]/sqrt(cov_p[i,i]*cov_p[j,j]))).rjust(6),end='')
            print()
        print() 

        print("Final Parameters:")
        print() 
        for i in range(npar):
            print(" p["+str(i)+"]"+\
                    " = %.5e +/- %.1e (%.2f%%)" %\
                    (p[i],dp[i],dp[i]/abs(p[i])*100.))
        print()

    return [p, dp, (res ** 2).mean()]
