# Mysql Connectors, and time ; 
import mysql.connector
import time
from datetime import datetime,timezone
import numpy as np 

# Multi-threading for controlling;
import threading

# Slow stage Position and RTD measurement;  
from mossbauer_control.instruments import keithley
# LOCK-IN-AMPLIFIER for fast stage; 
#from mossbauer_control.instruments import SRS830
#from mossbauer_control.instruments import SRS810
from mossbauer_control.instruments import SRS860
# Yoctopuce, the code is organized strangely
from mossbauer_control.instruments import Yoctopuce

# RTD Voltage Supply;
from mossbauer_control.instruments import dc205
# Fast Stage Function Generator
from mossbauer_control.instruments import DS360
# Slow Stage Function Generator
from mossbauer_control.instruments import K263
# Camera Trigger 
from mossbauer_control.instruments import bnc555

# CSV Savings;
import csv 
import os

# Command Line Parameters
import sys 
import argparse 



# This script includes three parts, the sql writer , the csv writer and the slowcontrol class itself; 
from decimal import Decimal, getcontext, ROUND_HALF_UP
getcontext().prec = 28
_Q12 = Decimal('0.000000000001')  
def _q12(x):
	return Decimal(str(x)).quantize(_Q12, rounding=ROUND_HALF_UP)



class sql_writer:
	def __init__(self,
				 host='192.168.2.2',
				 user='writer',
				 password='mossbauer_writer',
				 database='slowcontrol',
				 table='RTD'):
		self.table = table  
		self.conn = mysql.connector.connect(
			host=host, user=user, password=password, database=database,
			autocommit=True, connection_timeout=5
		)
		self.cur = self.conn.cursor()


	def insert_snapshot(self, t_dt_utc,
						diff_T, abs_T,
						current, data_V,
						A, A_set, phi, f_ref, f_set, H, P, T):
		try:
			self.conn.ping(reconnect=True, attempts=1, delay=0)
		except Exception:
			self.conn.reconnect(attempts=3, delay=1)
			self.cur = self.conn.cursor()

		sql = (f"INSERT INTO `{self.table}` "
			   "(`TIME`,`diff_T`,`abs_T`,`current`,`data_V`,`A`,`A_set`,`phi`,`f_ref`,`f_set`, `H`, `P`, `T`) "
			   "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
		vals = (
			t_dt_utc,
			_q12(diff_T), _q12(abs_T),
			_q12(current), _q12(data_V),
			_q12(A), _q12(A_set), _q12(phi), _q12(f_ref), _q12(f_set), _q12(H), _q12(P), _q12(T)
		)
		try:
			self.cur.execute(sql, vals)
		except Exception as e:
			print(f"[WARN] MySQL insert_snapshot failed: {e}")


class slowcontrol():    
	def __init__(self,scan_symbol,vf_symbol):
		self.drive = DS360(gpib_address = 8)
		# Fast Stage function generator;
		self.calibrator = K263(gpib_address = 9)
		# Slow Stage function generator;
		self.k  = 20e-6/170 # meter per volts, the piezo; 

		self.voltmeter = keithley(gpib_address = 6)
		# Slow stage position;
		#self.srs = SRS830(gpib_address = 10)
		self.srs = SRS860(gpib_address = 10)
		# Fast stage position;
		
		self.dc205 = dc205()
		# RTD voltage supply 
		self.thermo = keithley(gpib_address = 7)
		# RTD readout 
		
		self.bnc = bnc555(gpib_address = 1)
		# Camera Trigger;
		
		self.db = sql_writer(table='sc')
		
		# Velocity Scan? 
		self.scan = scan_symbol
		self.scan_velocity_integration_time=300
		self.scan_velocity_list = np.linspace(0.001e-3,0.55e-3,50)
		# Variable Frequency Scan? 
		self.vf = vf_symbol 
		self.vf_velocity_integration_time=300
		self.vf_velocity_list = np.linspace(0.001e-3,2.00e-3,100)
		
		
		# Parameters setup, it is also possible to read it from the config file; 
		self.RTD_voltage_set=2 
		self.RTD_voltage = self.RTD_voltage_set
		self.RTD_switch_interval = 10 
		
		#self.RTD_read_interval = 1  
		self.Slow_current_set = 0e-9 
		self.Slow_current=  self.Slow_current_set
		self.Slow_switch_interval = 500
		
		# Fast Stage parameters;
		self.fast_Vpp = 20
		self.fast_freq= 40 
		
		# BNC parameters
		# BNC shares the frequency with fast stage
		self.nbursts=5
		
		# Latest values;
		# Keithley Temperature Sensors;
		self.latest_diff_T=0
		self.latest_abs_T=0
		# Keithley slow stage voltage/length;
		self.latest_data_V=0
		# Lock-in-amplifier phase and amplitude; 
		self.latest_A  = 0 
		self.latest_phi = 0 
		self.latest_f = 0

	def vf_parameters(self,v): 
    
		# The frequency will always put the amplitude at A=38;
		self.fast_Vpp=38 
		self.fast_freq= v / ( np.pi * self.fast_Vpp * self.k)
		
		# The BNC will just take a 1ms frame at the center; 
		self.nbursts=1 
		self.bncdelay= max(0,round( 1/(4*self.fast_freq)- (1e-3)/2 , 4) ) 
	
	def RTD_Flip(self):
		'''
		Deprecated function; 
		  '''
		stop = threading.Event()
		def run():
			nextT = time.monotonic() + self.RTD_switch_interval  
			while not stop.is_set():
				if stop.wait(max(0.0, nextT - time.monotonic())):
					break
				self.RTD_voltage = -self.RTD_voltage
				self.dc205.set_voltage(self.RTD_voltage)
				nextT =time.monotonic()+ self.RTD_switch_interval    
		threading.Thread(target=run, daemon=True).start()
		return stop  
	
	def Slow_Flip(self): 
		'''
		A background thread that will flip the direction of current of the small stage; 
		  '''
		# the stop (thread.event) could be used to stop this thread
		stop = threading.Event()
		def run():
			nextT = time.monotonic() + self.Slow_switch_interval  
			self.calibrator.set_current(self.Slow_current)
			while not stop.is_set():
				if stop.wait(max(0.0, nextT - time.monotonic())):
					break
				self.Slow_current = -self.Slow_current
				self.calibrator.set_current(self.Slow_current)
				nextT =time.monotonic()+ self.Slow_switch_interval
				if self.Slow_current <0:
					self.calibrator.discharge()
					print('discharged')  
					self.calibrator.set_current(self.Slow_current)  
		threading.Thread(target=run, daemon=True).start()
		return stop 


	def set_to_v(self, v):
		#k = 20e-6/170 # meter per volts
		f = self.fast_freq
		V_pp = v / ( np.pi * f * self.k)
		offset = 0 # Keep the offset constant ; 
	
		self.fast_Vpp =V_pp
		self.drive.set_sine()
		self.drive.set_frequency(f)
		self.drive.set_Vpp(V_pp)
		self.drive.set_offset(offset)
		self.drive.output_on()



	def Velocity_scan(self): 
		'''
		A background thread that will change the A_set; 
	    '''
		# the stop (thread.event) could be used to stop this thread
		stop = threading.Event()
		def run():
			n = len(self.scan_velocity_list) # How many velocity we have 
			nextT = time.monotonic() + self.scan_velocity_integration_time  
			self.drive.set_Vpp(self.fast_Vpp)
			i=0 
			while not stop.is_set():
				
				if stop.wait(max(0.0, nextT - time.monotonic())):
					break
				self.set_to_v(self.scan_velocity_list[i])
				
				i= (i+1)%n 
				nextT =time.monotonic()+ self.scan_velocity_integration_time
		threading.Thread(target=run, daemon=True).start()
		return stop 
 
 
 
	def start_rtd_flip_and_thermo_poll(self, poll_interval: float = 0.2, settle_s: float = 0.2):
		#Replace the RTD_Flip and start_thermo_latest because we want to synchronize the readout. 
		stop = threading.Event()
		
		def run():
			now = time.monotonic()
			next_flip = now + self.RTD_switch_interval
			next_poll = now + poll_interval
		
			while not stop.is_set():
				target = min(next_flip, next_poll)
				if stop.wait(max(0.0, target - time.monotonic())):
					break
		
				now = time.monotonic()
		
				did_flip = False
				if now >= next_flip - 1e-9:
					try:
						self.RTD_voltage = -self.RTD_voltage
						self.dc205.set_voltage(self.RTD_voltage)
					except Exception as e:
						print(f"[WARN] RTD flip failed: {e}")
					did_flip = True
					next_flip += self.RTD_switch_interval
		
				if did_flip and settle_s > 0:
					if stop.wait(settle_s):
						break
		
				try:
					ch1, ch2 = self.thermo.measure_both()
					self.latest_diff_T = ch1
					self.latest_abs_T  = ch2
				except Exception as e:
					print(f"[WARN] thermo read failed: {e}")
		
				while next_poll <= now + 1e-9:
					next_poll += poll_interval
		
		threading.Thread(target=run, daemon=True).start()
		return stop

	
	def start_thermo_latest(self, poll_interval: float = 0.0):
		'''
		deprecated function that is used to readout the absolute temperature and relative temperature;
		  '''
		#not used?
		stop = threading.Event()
		def run():
			while not stop.is_set():
				t0 = time.time()
				try:
					# change the function if you want to use other ways to measure it;
					ch1, ch2 = self.thermo.measure_both()   
					self.latest_diff_T = ch1 
					self.latest_abs_T = ch2 
				except Exception as e:
					print(f"[WARN] thermo latest read failed: {e}")
					pass
				if poll_interval > 0:
					remain = poll_interval - (time.time() - t0)
					if remain > 0:
						if stop.wait(remain):
							break
		threading.Thread(target=run, daemon=True).start()
		return stop
	
	def yocto_latest(self, poll_interval: float = 0.0):
		'''
		temperature sensor; 
		  '''
		stop = threading.Event()
		def run():
			while not stop.is_set():
				t0 = time.time()
				try:
					self.latest_T, self.latest_P, self.latest_H = self.Y.measure()
				except Exception as e:
					print(f"[WARN] yoctopuce latest read failed: {e}")
					pass
				if poll_interval > 0:
					remain = poll_interval - (time.time() - t0)
					if remain > 0:
						if stop.wait(remain):
							break
		threading.Thread(target=run, daemon=True).start()
		return stop		
	
	def start_volt_latest(self, poll_interval: float = 0.0):
		'''
		Background thread that could read the position of the slow stage out;
		  '''
		stop = threading.Event()
		def run():
			while not stop.is_set():
				t0 = time.time()
				try:
					data_V = self.voltmeter.get_data()
					self.latest_data_V = data_V
				except Exception as e:
					print(f"[WARN] volt latest read failed: {e}")
					pass
				if poll_interval > 0:
					remain = poll_interval - (time.time() - t0)
					if remain > 0:
						if stop.wait(remain):
							break
		threading.Thread(target=run, daemon=True).start()
		return stop	

	def start_srs_latest(self, poll_interval: float = 0.0):
		'''
		The srs is the lockin amplifier; 
		  '''
		stop = threading.Event()
		def run():
			while not stop.is_set():
				t0 = time.time()
				try:
					(R, theta_ref, f_ref)  = self.srs.read_all()
					self.latest_A  = R 
					self.latest_phi = theta_ref
					self.latest_f = f_ref
				except Exception as e:
					print(f"[WARN] srs latest read failed: {e}")
					pass
				if poll_interval > 0:
					remain = poll_interval - (time.time() - t0)
					if remain > 0:
						if stop.wait(remain):
							break
		threading.Thread(target=run, daemon=True).start()
		return stop		
	
	def setup(self):
		# This script is mainly used to control the instruments that could output ;
		
		# Fast Stage Control and readout 
		#set up fast stage Function Generator;
		self.drive.experiment_setup(f=self.fast_freq,A=self.fast_Vpp) #why n bursts
		if self.scan : 
			self.drive_stopper=self.Velocity_scan()
		
		# setup SRS fast stage;
		self.srs.experiment_setup() #maybe add time const dep on frequency of readout
		self.srs_stopper=self.start_srs_latest(0.2)
		
		  #set up BNC555, trigger box;
		self.bnc.experiment_setup(self.fast_freq, self.nbursts)
		
		# Slow Stage control and readout 
		# Slow stage current source 
		self.calibrator.experiment_setup() #maybe we define the current?
		self.calibrator_stopper = self.Slow_Flip()
		# setup keithley slow stage ; 
		self.voltmeter.experiment_voltmeter_setup()
		self.volt_stopper = self.start_volt_latest(0.2)
		
		# RTD control and readout
		  # RTD Function Generator; 
		self.dc205.experiment_setup()
		#self.dc205_stopper = self.RTD_Flip()	
		# setup keithley RTD; 
		self.thermo.experiment_thermo_setup()
		#self.thermo_stopper=self.start_thermo_latest(0.2)
		self.rtd_thermo_stopper = self.start_rtd_flip_and_thermo_poll(poll_interval=0.2, settle_s=0.2)
  
		
		# setup yotocpuce;
		loggername_mossbauer = 'METEOMK2-2377A2'
		self.Y = Yoctopuce(loggername_mossbauer)
		self.Y_stopper= self.yocto_latest(poll_interval=0.6)
		
	
	def fetch(self,interval=1,max_seconds=None):
    	# This script is used to fetch the data from the instruments; 
		deadline = None if max_seconds is None else (time.time() + max_seconds)
		while True:
			t0 = time.time()
			ts= datetime.now(timezone.utc)
			
			# Use the snapshot to get the current value and then record it.  
			diff_T = getattr(self, 'latest_diff_T', -1)
			abs_T  = getattr(self, 'latest_abs_T',-1)
			rtd_V  = getattr(self, 'RTD_voltage', -1) 
			current= getattr(self, 'Slow_current',-1)
			data_V = getattr(self, 'latest_data_V', -1)
			
			A      = getattr(self, 'latest_A',-1)
			A_set  = getattr(self, 'fast_Vpp',-1)
			phi    = getattr(self, 'latest_phi',-1)
			f_ref  = getattr(self, 'latest_f',-1)
			f_set  = getattr(self, 'fast_freq', -1 )
		
			# The temperature sensor is also needed; 
			H		= getattr(self, 'latest_H', -1)
			P		= getattr(self, 'latest_P', -1)
			T		= getattr(self, 'latest_T', -1)
		
		
		
			remain = interval - (time.time() - t0)
			
			print(f"[{ts.isoformat()}] strain_small={data_V:.6g}  diff_T={diff_T:.6g}  abs_T={abs_T:.6g} "
			f"A={A:.6g} A_set {A_set}  phi={phi:.6g}  f={f_ref:.6g} (set {f_set})  I={current:.6g} H={H:.6g} P={P:.6g} T={T:.6g}")
			
			self.db.insert_snapshot(ts,
				diff_T, abs_T,
				current, data_V,
				A, A_set, phi, f_ref, f_set, H, P, T)
			
			# We have setup the autocommit by default, no need to commit it manually;
			#self.db.conn.commit()
			
			if remain > 0:
				time.sleep(remain)
		
			if deadline is not None and time.time() >= deadline:
				return

	def run(self):
		if self.vf: 
			n = len(self.vf_velocity_list)
			i=0 
			while True: 
				self.vf_parameters(self.vf_velocity_listp[i])
				self.setup()
				time.sleep(5)
				self.fetch(max_seconds=self.vf_velocity_integration_time)
				self.stop()
				time.sleep(5)
				i=(i+1)%n
		else:      
			self.setup()
			time.sleep(5)
			self.fetch()
		
	def stop(self):
		self.drive.output_off()
		self.bnc.close() 
		
		# Stop the threads; 
		self.calibrator_stopper.set()
		#self.dc205_stopper.set()
		self.volt_stopper.set()
		#self.thermo_stopper.set()
		self.srs_stopper.set()
		self.rtd_thermo_stopper.set()
		self.Y_stopper.set()
		
		# Stop the drive; 
		if self.scan: 
			self.drive_stopper.set() 	
 
	
	# Let us integrate the RTD script first; 
	



if __name__ == "__main__" :
		
	parser = argparse.ArgumentParser()
	argBool = lambda s: s.lower() in ['true', 't', 'yes', '1']
	
	parser.add_argument(
		"--scan", 
		type     = argBool,
		required = False,
		default  = False,
		help     = "Whether this is a scan;",
	) 

	parser.add_argument( 
        "--vf", 
        type     = argBool,
		required = False,
		default  = False,
        help = "Whether this is a variable frequency scan"            
    )
		
	args = parser.parse_args()	
		
	sc = slowcontrol(args.scan,args.vf)
	#sc.scan_velocity_list = 
	#sc.scan_mode = frequency/voltage
	try:
		sc.run()   
	except KeyboardInterrupt:
		print("\n[INFO] KeyboardInterrupt, stopping...")
	finally:
		sc.stop()
