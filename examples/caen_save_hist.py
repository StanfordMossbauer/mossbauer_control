
import time
from mossbauer_control.instruments import CAEN
from mossbauer_control.motor import Motor

motor = Motor( agilent = "GPIB0::14::INSTR",arduino = "/dev/ttyACM1")
caen = CAEN("/home/mossbauer_lab/mossbauer_control/caen_configs/co57_config")

savedir = r'/home/mossbauer_lab/Data/'

integration_time = 100

velocity = 5  #only positive velocities!

if velocity == 0:
	total_time = integration_time
	digi.timed_acquire(integration_time)

else:
	total_time = 0

	while total_time < integration_time:
		motor.velocity = velocity
		motor.start()

		while motor.flagA is False:
			 	time.sleep(0.01)

		caen.start()

		t1 = time.time()
		while motor.flagB is True:
		    time.sleep(0.01)       
		total_time += (time.time()-t1)

		caen.stop()

		time.sleep(0.1)
		motor.stop()

		#now go backwards same velocity

		motor.velocity = -5

		motor.start()
		while motor.flagA is True:
		    time.sleep(0.01)
		            
		time.sleep(0.1)
		motor.stop()


caen.update_count()



filename  = 'Hist_skim_550_1200_v_{:.2f}_t_{:.1f}_FeCy.txt'.format(velocity, total_time)

print('rate is {:.2f} Hz'.format(caen.count/total_time))
h = caen.histogram( savefile = savedir+filename, skim_lim_lower = 500, skim_lim_upper = 1250)


caen.close()
motor.close()