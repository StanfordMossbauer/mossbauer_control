from mossbauer_control.instruments import BK4060B, Agilent
import time
piezo  = BK4060B()

piezo.active = 1
piezo.mode = 'RAMP'
piezo.burststate = 'ON' #to do #syncronization with master clock
piezo.burstmode = 'NYC' # TRIG:Ncycles (TTL define start of the N cycles), GAT:Gated (TTL defined Output onor off)
piezo.burstcycles = 10 #to do #syncronization every 100 cycles
piezo.burstphase = -90 # phase between marter clock and drive signal
piezo.triggersource = 'EXT'
piezo.output = 'OFF'

piezo.active = 2
piezo.mode = 'SQUARE'
piezo.burststate = 'ON' #to do #syncronization with master clock
piezo.burstmode = 'NCYC' # TRIG:Ncycles (TTL define start of the N cycles), GAT:Gated (TTL defined Output onor off)
piezo.burstcycles = 10 #to do #syncronization every 100 cycles
piezo.burstphase = 0 # phase between marter clock and drive signal
piezo.triggersource = 'EXT'
piezo.output = 'OFF'

clock = Agilent("GPIB::14::INSTR")
clock.output = ('ON')
t0 = time.time()
time.sleep(1)
print(time.time()-t0)

frequencies = [50, 100]



for i in [0,1]:
	for piezo.active in [1,2]: #both channels
	    #print(piezo.active)
	    period = 1/frequencies[i]
	    cycles = int(0.1/period)
	    piezo.burstcycles = cycles
	    actualscanTime = cycles*period
	    print(piezo.device.ask("*OPC?"))   
	    piezo.frequency = frequencies[i]
	    #piezo.output='ON'
	    if piezo.output=='OFF': piezo.output='ON'
	    t0 = time.time()
	    print(piezo.device.ask("*OPC?"), time.time()-t0)

	time.sleep(0.1)
	clock.trigger()
	time.sleep(0.2)

	clock.trigger()
	time.sleep(0.2)
	clock.trigger()
	time.sleep(1)



piezo.close()
clock.close()
