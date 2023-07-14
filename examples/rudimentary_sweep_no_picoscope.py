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
#data_file = directory + 'test_run7.dat'

protect_overwrite = True#False



Vmax = 10
Vmin = 0
Xmax = 318e-3
Xmin = 0e-3



frequencies = np.linspace(0, 1, 9)#[np.linspace(0,0.5,51)[21]]#np.ones(5)# np.linspace(0, 150, 4)#
scanTime = 3/frequencies[1]

#frequencies = np.zeros(100)
#scanTime = 1
scanTime = max(scanTime, 10)

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
#skim.dutycycle = 
skim.device.write("PULSe:DCYCle 90")
skim.burststate = 1 
skim.burstmode = 'TRIG' 

skim.amplitude = 5
skim.offset = 2.5 # somehow the hp signal generator outputs a value that isd different from seeting. 1.3 gives 2.5
skim.triggersource = 'EXT'
skim.output = 'ON'

#set piezo motion (channel 1) 
piezo.active = 1
piezo.mode = 'RAMP'
piezo.burststate = 'ON' #to do #syncronization with master clock
piezo.burstmode = 'NCYC' # TRIG:Ncycles (TTL define start of the N cycles), GAT:Gated (TTL defined Output onor off)
piezo.burstcycles = 10 #to do #syncronization every 100 cycles
piezo.burstphase = -90 # phase between marter clock and drive signal
piezo.triggersource = 'EXT'
piezo.amplitude = Vmax-Vmin 
piezo.offset = (Vmax+Vmin)/2
piezo.output = 'OFF'

# set switch change (channel 2)
piezo.active =2
piezo.mode = 'SQUARE'
piezo.burststate = 'ON' #to do #syncronization with master clock
piezo.burstmode = 'NCYC' # TRIG:Ncycles (TTL define start of the N cycles), GAT:Gated (TTL defined Output onor off)
piezo.burstcycles = 10 #to do #syncronization every 100 cycles
piezo.burstphase = 0 # phase between marter clock and drive signal
piezo.triggersource = 'EXT'
piezo.amplitude = 5
piezo.offset = 2.5
piezo.output = 'OFF'


actual_velocity_list_ch_0 = []
actual_velocity_list_ch_1 = []

v_mean_squared_residual_ch_0 = []
v_mean_squared_residual_ch_1 = []

nominal_velocity_list_ch_0 = []
nominal_velocity_list_ch_1 = []

actual_scanTime_list = []

count_list_ch_0 = []
count_list_ch_1 = []

#this is to sync the 2 channels
time.sleep(scanTime)

prev_count = np.zeros(8, dtype=int)

for j in range(repetitions):
    for i in range(len(frequencies)):
        #print(frequencies[i])
        
        
        if frequencies[i]==0:
            piezo.active = 2
            piezo.burstcycles = 1
            piezo.frequency = 1/scanTime
            if piezo.output=='OFF': piezo.output='ON'; 
            piezo.active = 1
            if piezo.output=='ON': piezo.output='OFF';
            

            actualscanTime = scanTime
            #si = ps.setSamplingInterval(si[0], scanTime)
            
            #print(si)
        else:
            period = 1/frequencies[i]
            cycles = int(scanTime/period)
            actualscanTime = cycles*period

            skim.burstcycles = 2*cycles
            skim.frequency = 2*frequencies[i]

            piezo.active = 2 #switch
            piezo.burstcycles = cycles   
            piezo.frequency = frequencies[i]
            if piezo.output=='OFF': piezo.output='ON'

            piezo.active = 1 #position voltage
            piezo.burstcycles = cycles   
            piezo.frequency = frequencies[i]
            if piezo.output=='OFF': piezo.output='ON'; clock.device.write('*TRG'); time.sleep(2*scanTime)
                
            #si = ps.setSamplingInterval(si[0], period)
            #print(si)
            t1 = time.time()

        #ps.setSimpleTrigger(trigSrc="B", threshold_V=2.0, direction="Rising", delay=0, enabled=True, timeout_ms=0)
        #ps.runBlock()
        time.sleep(0.1)

        
        caen.start() #it takes a bit, ideally we have also a switch after this so we can wait!
        clock.device.write('*TRG')

        #t2 = time.time()

        t0 = time.time()
        while (time.time()-t0) <= actualscanTime:
            #print(time.time()-t0)
            time.sleep(actualscanTime/1000)
        caen.stop()
        caen.update_count()

        count_list_ch_0.append(caen.count[0] - prev_count[0])
        count_list_ch_1.append(caen.count[1] - prev_count[1])
        prev_count[0] = caen.count[0]
        prev_count[1] = caen.count[1]
        
        actual_scanTime_list.append(actualscanTime)

        time.sleep(scanTime/10)
        #t3 = time.time()
        #ps.waitReady()
        #t4 = time.time()
        data = [np.ones(1000),np.ones(1000)]
        #(data, nSamps, ovf) = ps.getDataRawBulkOld(['A', 'B'])



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
                    f.write(f'{nominal_velocity_list_ch_0[-1]}\t{actual_velocity_list_ch_0[-1]}\t{v_mean_squared_residual_ch_0[-1]}\t{count_list_ch_0[-1]}\t{actual_scanTime_list[-1]}\n')
                    f.write(f'{nominal_velocity_list_ch_1[-1]}\t{actual_velocity_list_ch_1[-1]}\t{v_mean_squared_residual_ch_1[-1]}\t{count_list_ch_1[-1]}\t{actual_scanTime_list[-1]}\n')

        #print('full scans: {}/{}, current iteration {}/{},  +/-{:.2f} mm/s ch_0: {:.2f} Hz ch_1: {:.2f} Hz'.format(j,repetitions, i,len(frequencies), actual_velocity_list_ch_0[-1], count_list_ch_0[-1]/scanTime, count_list_ch_1[-1]/scanTime))
        #print(t1-t0,t2-t1,t3-t2,t4-t3,t5-t4,time.time()-t5)
        print('full scans: {}/{}, current iteration {}/{},  +/-{:.2f} mm/s ch_0: {:.2f} Hz ch_1: {:.2f} Hz ratio: {:.2f}'.format(j,repetitions, i,len(frequencies), nominal_velocity_list_ch_0[-1], count_list_ch_0[-1]/scanTime, count_list_ch_1[-1]/scanTime, count_list_ch_0[-1]/count_list_ch_1[-1]))
        

#plt.show()

for piezo.active in [1,2]:
    piezo.output = "OFF"
clock.output = 'OFF'
skim.output = 'OFF'
piezo.close()
clock.close()
caen.close()
#ps.close()

