
import time
import os
from mossbauer_control.instruments import CAEN
#from mossbauer_control.motor import Motor
from datetime import datetime, timedelta

caen = CAEN("/home/mossbauer/mossbauer_control/caen_configs/co57_config_2ch")
directory = "/home/mossbauer/Data/{}_histograms/".format(time.strftime("%Y%m%d"))
channel = 0

if not os.path.isdir(directory): os.mkdir(directory)
    
absorber = 'prescantest'
integration_time = 10
detector_distance = 19 #in

print('integrating {} seconds, will finish at {}'.format(integration_time, datetime.now() + timedelta(seconds=integration_time)))
caen.timed_acquire(integration_time)
caen.update_count()

filename  = 'Hist_{}_{}s_{}in.txt'.format(absorber, integration_time,detector_distance)

print('rate is {:.2f} Hz'.format(caen.count[channel]/integration_time))
h = caen.histogram( readfile = 'Histo_0_0.txt',savefile = directory+filename)

caen.close()
