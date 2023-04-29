iimport time
import os
import numpy as np
from mossbauer_control.instruments import CAEN, Agilent, HP33120A
from picoscope import ps4000
import utility.utils as u
import matplotlib.pylab as plt
from tqdm import tqdm

directory = "/home/mossbauer_lab/Data/{}_scan/".format(time.strftime("%Y%m%d"))
data_file = directory + 'piezoscan_0.5_mms_0.01_mms_0.dat'


frequencies = np.linspace(0,0.5,51)
scanTime = 1/frequencies[1]
repetitions = 1000

def lin(p,x):
    a,b= p
    return a+b*x


if not os.path.isdir(directory):  # check this is he entering all time??
        try:
            os.mkdir(directory)
        except OSError:
            print("Creation of the directory %s failed" % directory)
        else:
            print("Successfully created the directory %s " % directory)

### avoids overwriting
ii=0
while os.path.isfile(data_file):
    ii+=1
    data_file = data_file[:-5]+str(ii)+'.dat'

if not os.path.exists(data_file):
    with open(data_file, 'w') as f:
            f.write('nom_vel\tvel\tmsr\tcount\tseconds\n')



piezo = Agilent("GPIB::14::INSTR")
clock = HP33120A("GPIB::15::INSTR")
caen = CAEN("/home/mossbauer_lab/mossbauer_control/caen_configs/co57_config_2ch")
ps = ps4000.PS4000()


ps.setChannel(channel='A', coupling='DC', VRange=10, VOffset=0.0, enabled=True)
ps.setChannel(channel='B', coupling='DC', VRange=10, VOffset=0.0, enabled=True)
samples_per_segment = ps.memorySegments(1)
ps.setNoOfCaptures(1)
si = [1e-4]




# set parameters
clock.mode = 'SQU'
clock.burststate = 1 #to do #syncronization with master clock
clock.burstmode = 'TRIG' # TRIG:Ncycles (TTL define start of the N cycles), GAT:Gated (TTL defined Output onor off)
clock.burstcycles = 1 #to do #syncronization every 100 cycles
clock.burstphase = 0 # phase between marter clock and drive signal
clock.triggersource = 'BUS'

piezo.mode = 'TRI'
piezo.burststate = 1 #to do #syncronization with master clock
piezo.burstmode = 'TRIG' # TRIG:Ncycles (TTL define start of the N cycles), GAT:Gated (TTL defined Output onor off)
piezo.burstcycles = 100 #to do #syncronization every 100 cycles
piezo.burstphase = -90 # phase between marter clock and drive signal
piezo.triggersource = 'EXT'
piezo.triggerslope = 'POS'
piezo.output = 'ON'


Vmax = 10
Vmin = -3
Xmax = 318e-3
Xmin = -95e-3

piezo.amplitude = Vmax-Vmin 
piezo.offset = (Vmax+Vmin)/2

clock.mode = 'SQU'
clock.amplitude = 2.5
clock.offset = 1.3 # somehow the hp signal generator outputs a value that isd different from seeting. 1.3 gives 2.5


actual_velocity_list_ch_0 = []
actual_velocity_list_ch_1 = []

v_mean_squared_residual_ch_0 = []
v_mean_squared_residual_ch_1 = []

nominal_velocity_list_ch_0 = []
nominal_velocity_list_ch_1 = []

actual_scanTime_list = []

count_list_ch_0 = []
count_list_ch_1 = []

prev_count = np.zeros(8, dtype=int)

for j in range(repetitions):
    for i in range(len(frequencies)):
        #print(frequencies[i])

        if frequencies[i]==0:
            clock.burstcycles = 1
            piezo.burstcycles = 1
            piezo.triggersource = 'BUS'
            clock.frequency = 1/scanTime
            actualscanTime = scanTime
            si = ps.setSamplingInterval(si[0], scanTime)
            #print(si)
        else:
            period = 1/frequencies[i]
            cycles = int(scanTime/period)
            actualscanTime = cycles*period
            piezo.triggersource = 'EXT'
            clock.burstcycles = cycles
            piezo.burstcycles = cycles
            piezo.frequency = frequencies[i]
            clock.frequency = frequencies[i]
            si = ps.setSamplingInterval(si[0], period)
            #print(si)


        ps.setSimpleTrigger(trigSrc="B", threshold_V=1.0, direction="Rising", delay=0, enabled=True, timeout_ms=0)
        ps.runBlock()
        time.sleep(0.1)

        clock.device.write('*TRG')
        t0 = time.time()
        caen.start()


        while (time.time()-t0) <= actualscanTime:
            time.sleep(actualscanTime/1000)
        caen.stop()

        time.sleep(scanTime/10)

        ps.waitReady()
        (data, nSamps, ovf) = ps.getDataRawBulkOld(['A', 'B'])

        caen.update_count()

        count_list_ch_0.append(caen.count[0] - prev_count[0])
        count_list_ch_1.append(caen.count[1] - prev_count[1])
        prev_count[0] = caen.count[0]
        prev_count[1] = caen.count[1]

        
        actual_scanTime_list.append(actualscanTime)

        #nominal velocity
        nominal_velocity_list_ch_0.append(2*(Xmax-Xmin)*frequencies[i])
        nominal_velocity_list_ch_1.append(-2*(Xmax-Xmin)*frequencies[i])

        #actual velocity (fit to strain gauge reading)
        tt = np.arange(len(data[0])//2)*si[0]
        x_p = data[0][:len(data[0])//2]*(20/2**16)*(Xmax-Xmin)/(Vmax-Vmin)
        x_n = data[0][len(data[0])//2:]*(20/2**16)*(Xmax-Xmin)/(Vmax-Vmin)

        p0 = [-0.1, 0.2]
        p_p,dp_p,res_p = u.fit_res(lin, tt, x_p, p0, fullout = False)

        p0[1] = -p_p[0]
        p_n,dp_n,res_n = u.fit_res(lin, tt, x_n, p0, fullout = False)

        actual_velocity_list_ch_0.append(p_p[1])
        v_mean_squared_residual_ch_0.append(res_p)

        actual_velocity_list_ch_1.append(p_n[1])
        v_mean_squared_residual_ch_1.append(res_n)
        #plt.plot(tt,x_p, '.')
        #plt.plot(tt,lin(p_p,tt), '.')



        with open(data_file, 'a') as f:
                    f.write(f'{nominal_velocity_list_ch_0[-1]}\t{actual_velocity_list_ch_0[-1]}\t{v_mean_squared_residual_ch_0[-1]}\t{count_list_ch_0[-1]}\t{actual_scanTime_list[-1]}\n')
                    f.write(f'{nominal_velocity_list_ch_1[-1]}\t{actual_velocity_list_ch_1[-1]}\t{v_mean_squared_residual_ch_1[-1]}\t{count_list_ch_1[-1]}\t{actual_scanTime_list[-1]}\n')

        print('full scans: {}/{}, current iteration {}/{},  +/-{:.2f} mm/s ch_0: {:.2f} Hz ch_1: {:.2f} Hz'.format(j,repetitions, i,len(frequencies), actual_velocity_list_ch_0[-1], count_list_ch_0[-1]/scanTime, count_list_ch_1[-1]/scanTime))


plt.show()

piezo.output = "OFF"
piezo.close()
clock.close()
caen.close()
ps.close()

