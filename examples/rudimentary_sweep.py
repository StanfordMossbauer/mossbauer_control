import time
import numpy as np
import os

from mossbauer_control.motor import Motor
from mossbauer_control.instruments import CAEN, TDS754A


motor = Motor( agilent = "GPIB0::14::INSTR",arduino = "/dev/ttyACM0")
caen = CAEN("/home/mossbauer_lab/mossbauer_control/caen_configs/co57_config")
TDS = TDS754A(resource = "GPIB0::13::INSTR") # TDS is Techtronix Digital Scope
    
print(TDS.read_identity())
TDS.freq_measurement_setup()
    
motor.resolution = 1

integration_time = 3600*1
stroke_length = 50 #mm

data_file = 'home/mossbauer_lab/Data/20230322_alphaFe.dat'

if not os.path.exists(data_file):
    with open(data_file, 'w') as f:
            f.write('vel\tcount\tseconds\n')


#calculate velocity list
velocity_list = np.array([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.2, 0.2, 0.3, 0.3, 0.3, 0.4,0.4,0.4,0.4,0.5,0.5,0.5,0.5,0.5])#np.arange(0.01,0.5,0.02)               #only positive
velocity_list = np.arange(1,2,0.5)
velocity_list = list(np.arange(3,4,0.01))*50
sweep_time_list = []
count_list = []
actual_velocity_list = []

prev_count = 0

if motor.flagA is True:
    print("not in the correct initial position. put stage at starting point")
else:
    print("start experiment")
    for i in range(len(velocity_list)):

            motor.velocity = velocity_list[i]

            motor.start()
            while motor.flagA is False: 
                time.sleep(0.01)
            
            caen.start()

            t1 = time.time()
            while motor.flagB is True:
                time.sleep(0.01)       
            sweep_time_list.append(time.time()-t1)

            caen.stop()

            caen.update_count()
            count_list.append(caen.count - prev_count)
            actual_velocity_list.append(motor.velocity)
            prev_count = caen.count
            
            with open(data_file, 'a') as f:
                f.write(f'{actual_velocity_list[-1]}\t{count_list[-1]}\t{sweep_time_list[-1]}\n')

            print('{:.2f} mm/s {:.2f} Hz'.format(actual_velocity_list[-1], count_list[-1]/sweep_time_list[-1]))


            time.sleep(0.1)
            motor.stop()

            #now go backwards same velocity

            motor.velocity = -velocity_list[i]

            motor.start()
            while motor.flagB is False:  
                time.sleep(0.01)
          
            caen.start()

            t1 = time.time()
            while motor.flagA is True:
                time.sleep(0.01)

            sweep_time_list.append(time.time()-t1)
            caen.stop()
            
            caen.update_count()
            count_list.append(caen.count - prev_count)
            actual_velocity_list.append(motor.velocity)
            prev_count = caen.count

            with open(data_file, 'a') as f:
                f.write(f'{actual_velocity_list[-1]}\t{count_list[-1]}\t{sweep_time_list[-1]}\n')

            print('{:.2f} mm/s {:.2f} Hz'.format(actual_velocity_list[-1], count_list[-1]/sweep_time_list[-1]))
                        
            time.sleep(0.1)
            motor.stop()


caen.close()
motor.close()
