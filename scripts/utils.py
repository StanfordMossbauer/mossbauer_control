


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


def fit_picoscope_data(
        Xrange,
        Vrange,
        frequency,
        data,
        gate,
        actualSamplingInfo,
        plot=False,
        save=False
    ):
    """Takes in picoscope data, fits a line, returns slope and err"""

    fs = 1/actualSamplingInfo[0]
    period = actualSamplingInfo[0]*actualSamplingInfo[1]
    cycles = int(period*frequency)

    clip = int(cycles/frequency*fs)//cycles*cycles

    data = data[:clip].reshape(cycles,-1).mean(axis = 0)
    gate = gate[:clip].reshape(cycles,-1).mean(axis = 0)

    dataP = data[:len(data)//2]
    maskP = gate[:len(data)//2] > gate.mean()
    dataN = data[len(data)//2:]
    maskN = gate[len(data)//2:] > gate.mean()

    dataN = dataN[maskN]
    dataP = dataP[maskP]

    line = lambda p, x: p[0] + p[1]*x  # fit function

    p0 = [5,1]
    xdataP = np.arange(len(dataP))/fs
    xdataN = np.arange(len(dataN))/fs

    try:
        pP, dpP, msrP = fit_residuals(line, xdataP, dataP, p0, fullout=False)
        pN, dpN, msrN = fit_residuals(line, xdataN, dataN, p0, fullout=False)
        
    except Exception as e:
        print('Picoscope data fit failed!')
        print(e)
        pP, dpP, msrP = np.ones(3)*np.nan
        pN, dpN, msrN = np.ones(3)*np.nan

    if plot:
        plt.figure()
        plt.plot(xdataP, dataP)
        plt.plot(xdataN, dataN)
        #plt.plot(xdataP, line(pP, xdataP))
        #plt.plot(xdataP, line(pN, xdataN))
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
