# Mysql Connectors, and time ; 
import mysql.connector
import time
from datetime import datetime,timezone

# Multi-threading for controlling;
import threading

# Slow stage Position and RTD measurement;  
from mossbauer_control.instruments import keithley
# LOCK-IN-AMPLIFIER for fast stage; 
from mossbauer_control.instruments import SRS830
# Yoctopuce, the code is organized strangely
# from mossbauer_control.instruments import yoctopuce

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
						A, A_set, phi, f_ref, f_set):
		try:
			self.conn.ping(reconnect=True, attempts=1, delay=0)
		except Exception:
			self.conn.reconnect(attempts=3, delay=1)
			self.cur = self.conn.cursor()

		sql = (f"INSERT INTO `{self.table}` "
			   "(`TIME`,`diff_T`,`abs_T`,`current`,`data_V`,`A`,`A_set`,`phi`,`f_ref`,`f_set`) "
			   "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
		vals = (
			t_dt_utc,
			_q12(diff_T), _q12(abs_T),
			_q12(current), _q12(data_V),
			_q12(A), _q12(A_set), _q12(phi), _q12(f_ref), _q12(f_set)
		)
		try:
			self.cur.execute(sql, vals)
		except Exception as e:
			print(f"[WARN] MySQL insert_snapshot failed: {e}")




class csv_writer():   
	# the csv writer will write data into the csv files; 
	1==1


class slowcontrol():    
	def __init__(self):
		self.drive = DS360(gpib_address = 8)
		# Fast Stage function generator;
		self.calibrator = K263(gpib_address = 9)
		# Slow Stage function generator;

		self.voltmeter = keithley(gpib_address = 6)
		# Slow stage position;
		self.srs = SRS830(gpib_address = 10)
		# Fast stage position;
		
		self.dc205 = dc205(address="ASRL3::INSTR")
		# RTD voltage supply 
		self.thermo = keithley(gpib_address = 7)
		# RTD readout 
		
		self.bnc = bnc555(gpib_address = 1)
		# Camera Trigger;
		
		self.db = sql_writer(table='sc')
		
		
		
		# Parameters setup, it is also possible to read it from the config file; 
		self.RTD_voltage_set=2 
		self.RTD_voltage = self.RTD_voltage_set
		self.RTD_switch_interval = 10 
		
		#self.RTD_read_interval = 1  
		self.Slow_current_set = 1e-9 
		self.Slow_current=  self.Slow_current_set
		self.Slow_switch_interval = 500 
		
		# Fast Stage parameters;
		self.fast_amp = 6.579
		self.fast_freq= 30 
		
		# BNC parameters
		self.nbursts=5 
		
		# RTD values;
		self.latest_diff_T=0
		self.latest_abs_T=0
		self.latest_data_V=0
		self.latest_A  = 0 
		self.latest_phi = 0 
		self.latest_f = 0
	

	
	def RTD_Flip(self):
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
		stop = threading.Event()
		def run():
			nextT = time.monotonic() + self.Slow_switch_interval  
			while not stop.is_set():
				if stop.wait(max(0.0, nextT - time.monotonic())):
					break
				self.Slow_current = -self.Slow_current
				self.calibrator.set_current(self.Slow_current)
				nextT =time.monotonic()+ self.Slow_switch_interval    
		threading.Thread(target=run, daemon=True).start()
		return stop 

 
	def start_rtd_flip_and_thermo_poll(self, poll_interval: float = 0.2, settle_s: float = 0.2):
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
		stop = threading.Event()
		def run():
			while not stop.is_set():
				t0 = time.time()
				try:
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
	
	def start_volt_latest(self, poll_interval: float = 0.0):
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
		stop = threading.Event()
		def run():
			while not stop.is_set():
				t0 = time.time()
				try:
					(R, theta, f_ref ) = self.srs.read_all()
					self.latest_A  = R 
					self.latest_phi = theta
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
		
		#set up fast stage Function Generator;
		self.drive.experiment_setup(self.fast_freq,self.nbursts)
		#set up BNC555
		self.bnc.experiment_setup(self.fast_freq, self.nbursts)
		
		# Slow stage current source 
		self.calibrator.experiment_setup()
		self.calibrator_stopper = self.Slow_Flip()
		

		
		# setup keithley slow stage ; 
		self.voltmeter.experiment_voltmeter_setup()
		self.volt_stopper = self.start_volt_latest(0.2)
		
  		# RTD Function Generator; 
		self.dc205.experiment_setup()
		#self.dc205_stopper = self.RTD_Flip()	
		# setup keithley RTD; 
		self.thermo.experiment_thermo_setup()
		#self.thermo_stopper=self.start_thermo_latest(0.2)
		self.rtd_thermo_stopper = self.start_rtd_flip_and_thermo_poll(poll_interval=0.2, settle_s=0.2)
  
  
		# setup SRS fast stage;
		self.srs.experiment_setup()
		self.srs_stopper=self.start_srs_latest(0.2)
		
		# setup yotocpuce;
		# Not yet; 
		
	
	def fetch(self,interval=1):
		# This script is used to fetch the data from the instruments; 

		while True:
			t0 = time.time()
			ts= datetime.now(timezone.utc)
			
			diff_T = getattr(self, 'latest_diff_T', -1)
			abs_T  = getattr(self, 'latest_abs_T',-1)
			
			current= getattr(self, 'Slow_current',0)
			data_V = getattr(self, 'latest_data_V', -1)
			
			A      = getattr(self, 'latest_A',-1)
			A_set  = getattr(self, 'fast_amp',-1)
			phi    = getattr(self, 'latest_phi',-1)
			f_ref  = getattr(self, 'latest_f',-1)
			f_set  = getattr(self, 'fast_freq', -1 )
			
			remain = interval - (time.time() - t0)
			
			print(f"[{ts.isoformat()}] V={data_V:.6g}  diff_T={diff_T:.6g}  abs_T={abs_T:.6g} "
			  f"A={A:.6g} (set {A_set})  phi={phi:.6g}  f={f_ref:.6g} (set {f_set})  I={current:.6g}")
			
			self.db.insert_snapshot(ts,
				diff_T, abs_T,
				current, data_V,
				A, A_set, phi, f_ref, f_set)
				
			#self.db.conn.commit()
			
			if remain > 0:
				time.sleep(remain)

	def run(self):
		self.setup()
		time.sleep(1)
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
		# This function will stop the system;     
	
	# Let us integrate the RTD script first; 
	



if __name__ == "__main__" : 
	sc = slowcontrol()
	try:
		sc.run()   
	except KeyboardInterrupt:
		print("\n[INFO] KeyboardInterrupt, stopping...")
	finally:
		sc.stop()
	
	