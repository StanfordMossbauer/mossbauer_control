import time
import os
import sys
import numpy as np
from mossbauer_control.instruments import CAEN, Agilent, HP33120A, PS4000, BK4060B
#from picoscope import ps4000
import mossbauer_control as m
import matplotlib.pylab as plt
from tqdm import tqdm

clock = Agilent("GPIB::14::INSTR")
skim = HP33120A("GPIB::15::INSTR")
piezo = BK4060B('USB0::62700::60984::575A23113::INSTR')
caen = CAEN("/home/mossbauer/mossbauer_control/caen_configs/co57_config_2ch")

frequency = 1.0  # hz

piezo.device.write("*RST")

clock.mode = 'PULSE'
clock.frequency = 1000
clock.amplitude = 5
clock.offset = 2.5 # somehow the hp signal generator outputs a value that isd different from seeting. 1.3 gives 2.5
clock.triggersource = 'BUS'
clock.output = 'ON'

skim.mode = 'SQU'
dutypercent = 50
skim.dutycycle = dutypercent
skim.burststate = 1 
skim.burstmode = 'TRIG' 
skim.burstphase = int(-360*(1-dutypercent/100)+10)
skim.amplitude = 5
skim.offset = 2.5 # somehow the hp signal generator outputs a value that isd different from seeting. 1.3 gives 2.5
skim.triggersource = 'EXT'
skim.burstcycles = 2  # for dummy sweep
skim.output = 'ON'


Vmax = 10
Vmin = 0
#set piezo motion (channel 1) 
piezo.active = 1
piezo.mode = 'RAMP'
piezo.burststate = 'ON' #to do #syncronization with master clock
piezo.burstmode = 'NCYC' # TRIG:Ncycles (TTL define start of the N cycles), GAT:Gated (TTL defined Output onor off)
piezo.burstcycles = 1 # for dummy sweep
piezo.burstphase = -90 # phase between marter clock and drive signal
piezo.triggersource = 'EXT'
piezo.amplitude = Vmax-Vmin 
piezo.offset = (Vmax+Vmin)/2
piezo.output = 'ON'

# set switch change (channel 2)
piezo.active = 2
piezo.mode = 'SQUARE'
piezo.burststate = 'ON' #to do #syncronization with master clock
piezo.burstmode = 'NCYC' # TRIG:Ncycles (TTL define start of the N cycles), GAT:Gated (TTL defined Output onor off)
piezo.burstcycles = 1 # for dummy sweep
piezo.burstphase = 0 # phase between marter clock and drive signal
piezo.triggersource = 'EXT'
piezo.amplitude = 5
piezo.offset = 2.5
piezo.output = 'ON'

scanTime = 400

period = 1/frequency
cycles = int(scanTime/period)
actualscanTime = cycles*period

assert frequency != 0
print('dummy sweep to reset')
clock.device.write('*TRG')
time.sleep(2*period)
time.sleep(25)

#switch upstream counting or not
skim.burstcycles = 2*cycles
skim.frequency = 2*frequency

#switch downstream: choosing channel
piezo.active = 2 #switch
piezo.burstcycles = cycles   
piezo.frequency = frequency

#stage moving otr not
piezo.active = 1 #position voltage
piezo.burstcycles = cycles   
piezo.frequency = frequency

print('real sweep')

caen.start() #it takes a bit, ideally we have also a switch after this so we can wait!
time.sleep(10)
clock.device.write('*TRG')
time.sleep(actualscanTime*1.5)
caen.stop()
caen.update_count()


print(caen.count)
