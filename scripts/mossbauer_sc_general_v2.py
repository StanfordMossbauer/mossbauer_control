# Mysql Connectors, and time ; 
import mysql.connector
import time
from datetime import datetime,timezone
import numpy as np 

import threading

from mossbauer_control.instruments import keithley

from mossbauer_control.instruments import SRS860
from mossbauer_control.instruments import Yoctopuce
from mossbauer_control.instruments import dc205
from mossbauer_control.instruments import SDG1062X
from mossbauer_control.instruments import DS360
from mossbauer_control.instruments import K263
from mossbauer_control.instruments import bnc555

import csv 
import os

import sys 
import argparse 


# This script includes three parts, the sql writer , the csv writer and the slowcontrol class itself; 
from decimal import Decimal, getcontext, ROUND_HALF_UP
getcontext().prec = 28
_Q12 = Decimal('0.000000000001')  
def _q12(x):
	return Decimal(str(x)).quantize(_Q12, rounding=ROUND_HALF_UP)



class sql_writer:
	def __init__(self,host='192.168.2.2', user='writer', password='mossbauer_writer',database='slowcontrol',table='RTD'):
		self.table = table  
		self.conn = mysql.connector.connect(host=host, user=user, password=password, database=database,autocommit=True, connection_timeout=5)
		self.cur = self.conn.cursor()

	def insert_snapshot(self, t_dt_utc, rtd_diff, rtd_abs, 
						sp_current_set, sp_strain, Vpp_set, f_set, 
						A, phi, f, H, P, T):
		
		try:
			self.conn.ping(reconnect=True, attempts=1, delay=0)
		except Exception:
			self.conn.reconnect(attempts=3, delay=1)
			self.cur = self.conn.cursor()

		sql = (f"INSERT INTO `{self.table}` "
			   "(`TIME`,`diff_T`,`abs_T`,`current`,`data_V`,`A_set`, `f_set`, `A`, `phi`, `f_ref`, `H`, `P`, `T`) "
			   "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
		vals = (
			t_dt_utc,
			_q12(rtd_diff), _q12(rtd_abs),
			_q12(sp_current_set), _q12(sp_strain),
			_q12(Vpp_set), _q12(f_set), 
			_q12(A), _q12(phi), _q12(f), _q12(H), _q12(P), _q12(T)
		)
		
		try:
			self.cur.execute(sql, vals)
		except Exception as e:
			print(f"[WARN] MySQL insert_snapshot failed: {e}")


class slowcontrol():    
	def __init__(self,mode='fixed'):
	
		# Instruments;
		self.fast_piezo_drive = DS360(gpib_address = 8) 									# Fast Stage function generator;
		self.slow_piezo_drive = K263(gpib_address = 9)  									# Slow Stage function generator;
		self.trigger_generator = SDG1062X("USB0::0xF4EC::0x1103::SDG1PA0C900622::INSTR")	# Camera Triggers generator;
		self.position_nanovoltmeter = keithley(gpib_address = 6)							# Nanovoltmeter for slow stage position;
		self.lock_in = SRS860(gpib_address = 10)											# Lock-in for fast stage position readout;
		self.RTD_voltagesupply = dc205(address="ASRL6::INSTR") 													# RTD voltage supply 
		self.RTD_nanovoltmeter = keithley(gpib_address = 7) 								# RTD readout 
		self.pulse_generator = bnc555(gpib_address = 1)										# Camera Trigger;
		self.yoctopuce = Yoctopuce('METEOMK2-2377A2')										# Yoctopuce for temperature, humidity and pressure;
		self.database = sql_writer(table='sc')
		


		# Latest values;
		self.latest_rtd_diff=0
		self.latest_rtd_abs=0
		self.latest_sp_strain=0
		self.latest_A  = 0 
		self.latest_phi = 0 
		self.latest_f = 0

		#Fundamental parameters;
		# Mode: 'fixed', 'scan'
		self.mode = mode

		#Fixed mode parameters;
		self.Vpp_set = 15
		self.piezo_frequency = 200
		self.camera_exposure_time = 1e-3

		#Scan Mode parameters;
		self.scan_vpp_list= np.append( np.array((0.001)), np.arange(0.3,38,0.3))
		self.scan_velocity_integration_time=600  #only for scan; how long we stay at each velocity;

		self.RTD_voltage_set = 2 
		self.rtd_switch_interval = 10 		
		self.sp_current_set = 0e-9
		self.slow_piezo_switch_interval = 500
		self.data_recording_interval = 1
		
		    

	@property
	def camera_daq_delay(self):
		return 0.25 / self.piezo_frequency 
        
	@property
	def camera_trigger_delay(self):
		return 0.5 / self.piezo_frequency - 0.5*self.camera_exposure_time
	
	@property
	def camera_duty_cycle(self):
		return 2*self.camera_exposure_time*self.piezo_frequency*100


	############################################################## THREADS ########################################################################

	def slow_piezo_flip_thread(self): 
		'''
		A background thread that will flip the direction of current of the small stage; 
		  '''
		stop = threading.Event()
		def run():

			self.sp_current_set = -self.sp_current_set #flip the current to make sure we start with the positive direction;

			while not stop.is_set():
				
				# Handle discharge once per cycle (at negative current)
				if self.sp_current_set < 0:
					self.slow_piezo_drive.discharge()
					print('discharged')  
					self.slow_piezo_drive.set_current(self.sp_current_set)

				# Flip current direction
				self.sp_current_set = -self.sp_current_set
				self.slow_piezo_drive.set_current(self.sp_current_set)


				# Wait for switch interval
				if stop.wait(self.slow_piezo_switch_interval):
					break		
					
		threading.Thread(target=run, daemon=True).start()
		return stop 



	def velocity_scan_thread(self): 
		'''
		A background thread that will change the Vpp_set; 
	    '''
		# the stop (thread.event) could be used to stop this thread
		stop = threading.Event()
		def run():
			n = len(self.scan_vpp_list)
			i = 0
			
			while not stop.is_set():
				# Set current velocity
				self.Vpp_set = self.scan_vpp_list[i]
				self.fast_piezo_drive.set_Vpp(self.Vpp_set)
				
				# Measure at this velocity
				if stop.wait(self.scan_velocity_integration_time):
					break # Stop signal received - exit immediately
					
				# Move to next velocity
				i = (i + 1) % n

		threading.Thread(target=run, daemon=True).start()
		return stop 
 
 
 
	def rtd_flip_and_poll_thread(self, poll_interval: float = 0.2, settle_s: float = 0.2):
		#Replace the RTD_Flip and start_thermo_latest because we want to synchronize the readout. 
		stop = threading.Event()
		
		def run():
			last_flip_time = 0
			last_poll_time = 0
			
			while not stop.is_set():
				now = time.monotonic()
				
				# Check if it's time to flip RTD voltage
				if now - last_flip_time >= self.rtd_switch_interval:
					self.RTD_voltage_set = -self.RTD_voltage_set
					self.RTD_voltagesupply.set_voltage(self.RTD_voltage_set)
					last_flip_time = now
					
					# Wait for settling after flip
					if settle_s > 0:
						if stop.wait(settle_s):
							break
				
				# Check if it's time to poll temperature
				if now - last_poll_time >= poll_interval:
					ch1, ch2 = self.RTD_nanovoltmeter.measure_both()
					self.latest_rtd_diff = ch1
					self.latest_rtd_abs  = ch2
					last_poll_time = now
				
				# Short wait before next check
				if stop.wait(0.1):
					break
		
		threading.Thread(target=run, daemon=True).start()
		return stop

	
	
	def yocto_poll_thread(self, poll_interval: float = 0.6):
		'''
		temperature sensor; 
		  '''
		stop = threading.Event()
		def run():
			while not stop.is_set():
				# Poll sensor
				self.latest_T, self.latest_H, self.latest_P = self.yoctopuce.measure()
				
				# Wait for poll interval
				if stop.wait(poll_interval):
					break
					
		threading.Thread(target=run, daemon=True).start()
		return stop		
	
	def slow_piezo_poll_thread(self, poll_interval: float = 0.2):
		'''
		Background thread that could read the position of the slow stage out;
		  '''
		stop = threading.Event()
		def run():
			while not stop.is_set():
				# Poll position
				data_V = self.position_nanovoltmeter.get_data()
				self.latest_sp_strain = data_V
				
				# Wait for poll interval
				if stop.wait(poll_interval):
					break
					
		threading.Thread(target=run, daemon=True).start()
		return stop	

	def fast_piezo_poll_thread(self, poll_interval: float = 0.2):
		'''
		The srs is the lockin amplifier; 
		  '''
		stop = threading.Event()
		def run():
			while not stop.is_set():
				# Poll lock-in amplifier
				(R, theta_ref, f_ref) = self.lock_in.read_all()
				self.latest_A = R 
				self.latest_phi = theta_ref
				self.latest_f = f_ref
				
				# Wait for poll interval
				if stop.wait(poll_interval):
					break
					
		threading.Thread(target=run, daemon=True).start()
		return stop		
	


	############################################################## OPERATION FUNCTIONS ########################################################################


	def start_instruments(self):
		print("[INFO] Starting instrument setup...")

		#Setup the instruments;		
		print("[INFO] Setting up fast piezo drive...")
		self.fast_piezo_drive.experiment_setup(f=self.piezo_frequency,Vpp=self.Vpp_set)
		
		print("[INFO] Setting up lock-in amplifier...")
		self.lock_in.experiment_setup()
		
		print("[INFO] Setting up trigger generator...")
		self.trigger_generator.experiment_setup(frequency=self.piezo_frequency, delay_ch1=self.camera_trigger_delay, delay_ch2=self.camera_daq_delay, duty_cycle_ch1=self.camera_duty_cycle)

		print("[INFO] Setting up slow piezo drive...")
		self.slow_piezo_drive.experiment_setup()
		
		print("[INFO] Setting up position nanovoltmeter...")
		self.position_nanovoltmeter.experiment_voltmeter_setup()

		print("[INFO] Setting up RTD voltage supply...")
		self.RTD_voltagesupply.experiment_setup()
		
		print("[INFO] Setting up RTD nanovoltmeter...")
		self.RTD_nanovoltmeter.experiment_thermo_setup()	


	def start_threads(self):

		# Start the threads;
		print("[INFO] Starting monitoring threads...")
		
		print("[INFO] Starting fast piezo polling thread...")
		self.fast_piezo_poll_stopper=self.fast_piezo_poll_thread(0.2)
		
		print("[INFO] Starting slow piezo polling thread...")
		self.slow_piezo_poll_stopper = self.slow_piezo_poll_thread(0.2)
		
		print("[INFO] Starting Yoctopuce environmental sensor thread...")
		self.yocto_poll_stopper= self.yocto_poll_thread(poll_interval=0.6)
		
		print("[INFO] Starting RTD temperature monitoring thread...")
		self.rtd_flip_and_poll_stopper = self.rtd_flip_and_poll_thread(poll_interval=0.2, settle_s=0.2)

		
		if self.mode == 'scan': 
			print("[INFO] Configuring scan mode - setting piezo current to 0...")
			self.sp_current_set = 0e-9
			print("[INFO] Starting velocity scan thread...")
			self.velocity_scan_stopper=self.velocity_scan_thread()
		if self.mode == 'fixed':
			print("[INFO] Configuring fixed mode - starting piezo current flip thread...")
			self.slow_piezo_flip_stopper = self.slow_piezo_flip_thread()
		
		print("[INFO] All instruments and threads started successfully!")
	
		
	
	def start_data_recording(self):
		# This method fetches and logs data from all instruments 
		print("Beginning data recoring...")
		while True:
			t0 = time.time()
			ts= datetime.now(timezone.utc)
			
			# Use the snapshot to get the current value and then record it.  
			rtd_diff = getattr(self, 'latest_rtd_diff', -1)
			rtd_abs  = getattr(self, 'latest_rtd_abs',-1)
			sp_current_set= getattr(self, 'sp_current_set',-1)
			sp_strain = getattr(self, 'latest_sp_strain', -1)
			
			Vpp_set  = getattr(self, 'Vpp_set',-1)
			f_set  = getattr(self, 'piezo_frequency', -1 )
			A      = getattr(self, 'latest_A',-1)
			phi    = getattr(self, 'latest_phi',-1)
			f  = getattr(self, 'latest_f',-1)
		
			# The temperature sensor is also needed; 
			H		= getattr(self, 'latest_H', -1)
			P		= getattr(self, 'latest_P', -1)
			T		= getattr(self, 'latest_T', -1)
		
			remain = self.data_recording_interval - (time.time() - t0)
			
			print(f"[{ts.isoformat()}] strain_small={sp_strain:.3e}  rtd_diff={rtd_diff:.4e}  rtd_abs={rtd_abs:.4e} "
			f"A={A:.3e} Vpp_set {Vpp_set}  phi={phi:.1f}  f={f:.1f} (set {f_set})  sp_current={sp_current_set:.1e} H={H:.1f} P={P:.2f} T={T:.2f}")
			
			self.database.insert_snapshot(ts,
				rtd_diff, rtd_abs,
				sp_current_set, sp_strain,
				Vpp_set, f_set,
				A, phi, f, H, P, T)
				
			if remain > 0:
				time.sleep(remain)
		

		
	def stop(self):

		self.fast_piezo_drive.output_off()
		self.pulse_generator.close()
		self.yoctopuce.close()

		# Stop the threads; 
		self.rtd_flip_and_poll_stopper.set()
		self.slow_piezo_poll_stopper.set()
		self.fast_piezo_poll_stopper.set()
		self.yocto_poll_stopper.set()
		
		# Stop the drive; 
		if self.mode == 'scan': 
			self.velocity_scan_stopper.set() 
		if self.mode == 'fixed':
			self.slow_piezo_flip_stopper.set()	# Does this set current to 0? TODO: Check!
 


	############################################################## MAIN RUN ########################################################################

if __name__ == "__main__" :
		
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--mode",
		default='fixed',
		choices=['fixed', 'scan'],
		help="Measurement mode: 'fixed' for single velocity, 'scan' for velocity scanning"
	)
	args = parser.parse_args()

	#HERE SET PARMAETERS	
	slow_control = slowcontrol(mode=args.mode)

	slow_control.Vpp_set = 15
	slow_control.piezo_frequency = 200
	slow_control.camera_exposure_time = 1e-3
	
	slow_control.scan_vpp_list= np.append( np.array((0.001)), np.arange(0.3,38,0.3))
	slow_control.scan_velocity_integration_time=300
	slow_control.data_recording_interval = 1


	try:
		slow_control.start_instruments()
		slow_control.start_threads()
		time.sleep(5)
		slow_control.start_data_recording()

	except KeyboardInterrupt:
		print("\n[INFO] KeyboardInterrupt, stopping...")
	finally:
		slow_control.stop()

