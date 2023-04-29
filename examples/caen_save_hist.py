
import time
import os
from mossbauer_control.instruments import CAEN
from mossbauer_control.motor import Motor

caen = CAEN("/home/mossbauer_lab/mossbauer_control/caen_configs/co57_config")
directory = "/home/mossbauer_lab/Data/{}_Histograms/".format(time.strftime("%Y%m%d"))

if not os.path.isdir(directory): os.mkdir(directory)
    
absorber = 'FeCy'
integration_time = 100
detector_distance = 19 #in

print('integrating {} seconds, will finish at {}'.format(integration_time, datetime.now() + timedelta(seconds=integration_time)))
caen.timed_acquire(integration_time)
caen.update_count()

filename  = 'Hist_{}_{}s_{}in.txt'.format(absorber, total_time,detector_distance)

print('rate is {:.2f} Hz'.format(caen.count/total_time))
h = caen.histogram( readfile = 'Histo_0_0.txt',savefile = directory+filename)

caen.close()
