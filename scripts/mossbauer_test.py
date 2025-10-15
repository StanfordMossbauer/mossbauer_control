import time

from DS360 import DS360
from K263 import K263
#from SRSDC205 import dc205
from bnc555 import bnc


drive = DS360(gpib_address = 8)
calibrator = K263(gpib_address = 9)
#dc205 = dc205()
bnc = bnc(gpib_address = 1)


#set up fast stage
amp = 6.579
offset_V = amp/2
drive.set_sine()
drive.set_frequency(30)
drive.set_amplitude(amp)
drive.set_offset(offset_V)
drive.output_on()


#set up BNC555
bnc.setup()
bnc.reset()
#configure sys clock for 300Hz from 60Hz trigger
bnc.set_clock_mode('BURST')
bnc.set_ext_trigger()
bnc.enable(0, 'ON')
bnc.set_clock_f(0.00032)
bnc.burst_count(0, 5)
#set channel 1 for camera trigger
bnc.enable(1, 'ON')
bnc.channel_mode(1, 'BURST')
bnc.burst_count(1, 5)
bnc.pulse_width(1, 0.0001)
bnc.pulse_delay(1, 0)
#set channel 2 for camera DAQ
bnc.enable(2, 'ON')
bnc.channel_mode(2, 'BURST')
bnc.burst_count(2, 4)
bnc.pulse_width(2, 0.0001)
bnc.pulse_delay(2, 0.031)



#set up slow stage and RTD V supply
calibrator.set_current_mode()
calibrator.set_current_range()
calibrator.set_current(5E-9)
calibrator.operate()
#dc205.output_on()
i=0
while True:
    calibrator.set_current(1E-9)
    #dc205.set_voltage(2)
    time.sleep(500)
    calibrator.set_current(-1E-9)
    #dc205.set_voltage(-2)
    time.sleep(500)
    i+=1
calibrator.stop()
#dc205.close()






