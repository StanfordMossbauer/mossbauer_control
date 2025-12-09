import numpy as np
import pyvisa as pyvisa
import time as time

rm = pyvisa.ResourceManager ()
instr = rm.open_resource ("GPIB0::19::INSTR")

while True:
	f = open ("temperatures.txt", "a")
	f.write (f"{time.time ()},")
	for i in range (16):
		meas = instr.query (f"MEAS? {i + 1}").strip ()
		if float (meas) < 10000: f.write (f"{meas},")
	f.write ("\n")
	f.close ()




