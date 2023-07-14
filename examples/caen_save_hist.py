
import time
import os
from mossbauer_control.instruments import CAEN
#from mossbauer_control.motor import Motor
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

plot = True
channels = [1]

caen = CAEN("/home/mossbauer/mossbauer_control/caen_configs/co57_config_2ch")
directory = "/home/mossbauer/Data/{}_histograms/".format(time.strftime("%Y%m%d"))

if not os.path.isdir(directory): os.mkdir(directory)
    
absorber = 'Ferrocyanide'
integration_time = 100
detector_distance = 17 #in

print('integrating {} seconds, will finish at {}'.format(integration_time, datetime.now() + timedelta(seconds=integration_time)))
caen.timed_acquire(integration_time)
caen.update_count()


h = []

for channel in channels:
	print('rate is {:.2f} +/- {:.2f} Hz'.format(
        caen.count[channel]/integration_time,
        np.sqrt(caen.count[channel])/integration_time,
    ))
	filename  = 'Hist_{}_{}_{}s_{}in.txt'.format(channel, absorber, integration_time,detector_distance)
	h.append(caen.histogram( readfile = 'Histo_0_{}.txt'.format(channel),savefile = directory+filename))

	if plot:
		plt.plot(h[-1])
plt.show()

caen.close()

