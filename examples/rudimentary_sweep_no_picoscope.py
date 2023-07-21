import time
import os
import sys
import numpy as np
from mossbauer_control.instruments import CAEN, Agilent, HP33120A, PS4000, BK4060B
#from picoscope import ps4000
import mossbauer_control as m
import matplotlib.pylab as plt
from tqdm import tqdm

directory = "/home/mossbauer/Data/{}_scan/".format(time.strftime("%Y%m%d"))
#data_file = directory + 'Fe0004_0.5_mms_0.01_mms_19in.dat'
#data_file = directory + 'BeBlankUnpolished_1_mms_0.05_mms_19in.dat'
#data_file = directory + 'Fe0004_1_mms_0.05_mms_19in.dat'
#data_file = directory + 'Fe0004_1_mms_0.05_mms_19in_cardboard.dat'
data_file = directory + 'FeCy_0.6_mms_9steps_0.6-17in.dat'
data_file = directory + 'Fe0004_0vel_1step_0.6-17in_noskim_darknoise.dat'
data_file = directory + 'Fe0004_0.9_mms_13steps_0.6-17in.dat'
#data_file = directory + 'Fe0004_0.6_mms_outersteps_0.6-17in.dat'

#protect_overwrite = False
protect_overwrite = True


Vmax = 10
Vmin = 0
Xmax = 318e-3
Xmin = 0e-3



frequencies = np.linspace(0, 1, 9)#[np.linspace(0,0.5,51)[21]]#np.ones(5)# np.linspace(0, 150, 4)#
frequencies = np.linspace(0, 1.5, 13)#[-4:]
#frequencies = np.array([0.1,0.1])#np.linspace(0, 1.5, 13)#[-4:]
#scanTime = 3/frequencies[1]
scanTime = 24
if scanTime<(1/frequencies[1:].min()): print("Careful too shot time for lower frequency")

#for testing
#frequencies = np.ones(100)
#frequencies = np.zeros(100)
#scanTime = 10


vellist = frequencies*(2*(Xmax-Xmin))
repetitions = 1000

def lin(p,x):
    a,b= p
    return a+b*x


if not os.path.isdir(directory): os.mkdir(directory)

if protect_overwrite:
    ## avoids overwriting
    if os.path.isfile(data_file): 
        print('filename exists choose another one!') 
        sys.exit()

with open(data_file, 'w') as f:
        f.write('nom_vel\tvel\tmsr\tcount\tseconds\n')



clock = Agilent("GPIB::14::INSTR")
skim = HP33120A("GPIB::15::INSTR")
piezo = BK4060B('USB0::62700::60984::575A23113::INSTR')
caen = CAEN("/home/mossbauer/mossbauer_control/caen_configs/co57_config_2ch")
#ps = PS4000()


#ps.setChannel(channel='A', coupling='DC', VRange=10, VOffset=0.0, enabled=True)
#ps.setChannel(channel='B', coupling='DC', VRange=10, VOffset=0.0, enabled=True)
#samples_per_segment = ps.memorySegments(1)
#ps.setNoOfCaptures(1)
si = [1e-4]

piezo.device.write("*RST")

clock.mode = 'PULSE'
clock.frequency = 1000
clock.amplitude = 5
clock.offset = 2.5 # somehow the hp signal generator outputs a value that isd different from seeting. 1.3 gives 2.5
clock.triggersource = 'BUS'
clock.output = 'ON'

skim.mode = 'SQU'
dutypercent = 50
skim.frequency = 1
skim.dutycycle = dutypercent
#skim.device.write("PULSe:DCYCle 50")
skim.burststate = 1 
skim.burstmode = 'TRIG' 
skim.burstphase = int(-360*(1-dutypercent/100)+10)
#print(skim.burstphase)
skim.amplitude = 5
skim.offset = 2.5 # somehow the hp signal generator outputs a value that isd different from seeting. 1.3 gives 2.5
skim.triggersource = 'EXT'
skim.burstcycles = 2  # for dummy sweep
skim.output = 'ON'

#set piezo motion (channel 1) 
piezo.active = 1
piezo.mode = 'RAMP'
piezo.frequency = 1
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
piezo.frequency = 1
piezo.burststate = 'ON' #to do #syncronization with master clock
piezo.burstmode = 'NCYC' # TRIG:Ncycles (TTL define start of the N cycles), GAT:Gated (TTL defined Output onor off)
piezo.burstcycles = 1 # for dummy sweep
piezo.burstphase = 0 # phase between marter clock and drive signal
piezo.triggersource = 'EXT'
piezo.amplitude = 5
piezo.offset = 2.5
piezo.output = 'ON'

scanTime = 24

actual_velocity_list_ch_0 = []
actual_velocity_list_ch_1 = []

v_mean_squared_residual_ch_0 = []
v_mean_squared_residual_ch_1 = []

nominal_velocity_list_ch_0 = []
nominal_velocity_list_ch_1 = []

actual_DAQTime_list = []

count_list_ch_0 = []
count_list_ch_1 = []


prev_count = np.zeros(8, dtype=int)


print('dummy scan')
#### Dummy Scan ####
clock.device.write('*TRG')
#time.sleep(2*period)
time.sleep(5)
#####################
print('dummy scan done')
for j in range(repetitions):
    for i,frequency in enumerate(frequencies):
        if frequency==0:
            piezo.active = 1
            piezo.output = 'OFF'
            assert frequencies[0]==0
            frequency = frequencies[1:].min()
        else:
            piezo.active = 1
            print('reset piezo')
            if piezo.output=='OFF':
                piezo.output = 'ON'

        period = 1/frequency
        cycles = int(scanTime/period)
        actualscanTime = cycles*period

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
####TODO REMOVE#####
##### setting all speeds to zero
       # if piezo.output=='ON': piezo.output = 'OFF';

        caen.start() #it takes a bit, ideally we have also a switch after this so we can wait!
        time.sleep(1)  # TODO: remove when everything working
        clock.device.write('*TRG')

        print('sleep for %d secs' % actualscanTime)
        time.sleep(actualscanTime)
        time.sleep(1)  # TODO: remove when everything working
        caen.stop()
        caen.update_count()
        caen.histogram()



        count_list_ch_0.append(caen.count[0] - prev_count[0])
        count_list_ch_1.append(caen.count[1] - prev_count[1])

        prev_count[0] = caen.count[0]
        prev_count[1] = caen.count[1]
        
        # this is the time that gets used to calculate the rate
        actual_DAQTime_list.append(actualscanTime/2*dutypercent/100)

        data = [np.ones(1000),np.ones(1000)]

        #nominal velocity
        nominal_velocity_list_ch_0.append(2*(Xmax-Xmin)*frequencies[i])
        nominal_velocity_list_ch_1.append(-2*(Xmax-Xmin)*frequencies[i])

        #actual velocity (fit to strain gauge reading)
        tt = np.arange(len(data[0])//2)*si[0]
        x_p = data[0][:len(data[0])//2]*(20/2**16)*(Xmax-Xmin)/(Vmax-Vmin)
        x_n = data[0][len(data[0])//2:]*(20/2**16)*(Xmax-Xmin)/(Vmax-Vmin)

        p0 = [-0.1, 0.2]
        p_p,dp_p,res_p = m.fit_residuals(lin, tt, x_p, p0, fullout = False)

        p0[1] = -p_p[0]
        p_n,dp_n,res_n = m.fit_residuals(lin, tt, x_n, p0, fullout = False)

        actual_velocity_list_ch_0.append(p_p[1])
        v_mean_squared_residual_ch_0.append(res_p)

        actual_velocity_list_ch_1.append(p_n[1])
        v_mean_squared_residual_ch_1.append(res_n)
        #plt.plot(tt,x_p, '.')
        #plt.plot(tt,lin(p_p,tt), '.')

        #t5 = time.time()

        with open(data_file, 'a') as f:
                    f.write(f'{nominal_velocity_list_ch_0[-1]}\t{actual_velocity_list_ch_0[-1]}\t{v_mean_squared_residual_ch_0[-1]}\t{count_list_ch_0[-1]}\t{actual_DAQTime_list[-1]}\n')
                    f.write(f'{nominal_velocity_list_ch_1[-1]}\t{actual_velocity_list_ch_1[-1]}\t{v_mean_squared_residual_ch_1[-1]}\t{count_list_ch_1[-1]}\t{actual_DAQTime_list[-1]}\n')

        #print('full scans: {}/{}, current iteration {}/{},  +/-{:.2f} mm/s ch_0: {:.2f} Hz ch_1: {:.2f} Hz'.format(j,repetitions, i,len(frequencies), actual_velocity_list_ch_0[-1], count_list_ch_0[-1]/scanTime, count_list_ch_1[-1]/scanTime))
        #print(t1-t0,t2-t1,t3-t2,t4-t3,t5-t4,time.time()-t5)
        print('full scans: {}/{}, current frequency {:.3f},  +/-{:.2f} mm/s ch_0: {:.2f} Hz ch_1: {:.2f} Hz ratio: {:.2f}'.format(j,repetitions,frequencies[i], nominal_velocity_list_ch_0[-1], count_list_ch_0[-1]/actual_DAQTime_list[-1], count_list_ch_1[-1]/actual_DAQTime_list[-1], count_list_ch_0[-1]/count_list_ch_1[-1]))
        

#plt.show()

for piezo.active in [1,2]:
    piezo.output = "OFF"
clock.output = 'OFF'
skim.output = 'OFF'
piezo.close()
clock.close()
caen.close()
#ps.close()

