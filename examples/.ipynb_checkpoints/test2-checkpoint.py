import matplotlib.pyplot as plt
import numpy as np
from mossbauer_control.utils import fit_residuals


data = np.fromfile('../psdata_ramp.dat')
gate = np.fromfile('../psdata_gate.dat')

frequency  = 0.0625#0.125
fs = 1/0.00524288
period = 40
cycles = int(period*frequency)



clip = int(cycles/frequency*fs)//cycles*cycles



data = data[:clip].reshape(cycles,-1).mean(axis = 0)
gate = gate[:clip].reshape(cycles,-1).mean(axis = 0)

#plt.plot(np.arange(len(data))/fs, data)
#plt.plot(np.arange(len(data))/fs, gate)

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

pP, dpP, msrP = fit_residuals(slope, xdataP, dataP, p0, fullout=False)
pN, dpN, msrN = fit_residuals(slope, xdataN, dataN, p0, fullout=False)



plt.plot(xdataP, dataP)
plt.plot(xdataN, dataN)
plt.plot(xdataP, slope(pP, xdataP))
plt.plot(xdataP, slope(pN, xdataN))