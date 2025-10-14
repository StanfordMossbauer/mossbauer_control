import time
import matplotlib.pyplot as plt 
import numpy as np
import csv 
import os
import pandas as pd
from datetime import datetime


import mysql.connector
# Mysql Connectors; 

from mossbauer_control.instruments import keithley
# Slow stage and RTD measurement;  

from mossbauer_control.instruments import dc205
# RTD Voltages


def insert_rtd(cursor, t_dt, diff_T, abs_T):
	cursor.execute(
		"INSERT INTO RTD (`time`, `diff_T`, `abs_T`) VALUES (%s, %s, %s)",
		(t_dt, Decimal(str(diff_T)), Decimal(str(abs_T)))
	)

#or we can create a new csv file every day
def get_file_path(base_dir):
	"""Generate file path with current date"""
	date_str = datetime.now().strftime("%Y-%m-%d")
	filename = f"RTD_{date_str}.csv"
	return os.path.join(base_dir, filename)


# Instrument Parameters
dc205 = dc205()
thermo = keithley(gpib_address = 7)
dc205.output_on()
# In principle, it should be also recorded.. 
voltage = 2
switch_interval = 10 
read_interval = 1   



# It is fine to write down the password here because 
# - The database is only accessible via LAN;
# - The writer could only read and "add" data to the database, could not delete; 
conn= mysql_connector.connect(host='192.168.1.2',user='writer',password='mossbauer_writer',database='slowcontrol')
cur=conn.cursor()


# CSV Parameters 
# Folder to save CSVs
base_dir = r'C:\Users\mossbauer\Documents\data\1008'
os.makedirs(base_dir, exist_ok=True)
# Track current file date
current_day = datetime.now().date()
file_path = get_file_path(base_dir)



start_time = time.time()
last_switch_time = start_time

while True:
	now = datetime.now()
	if now.date() != current_day:
		# New day, create a new file
		current_day = now.date()
		file_path = get_file_path(base_dir)
		with open(file_path, mode='w', newline='') as file:
			writer = csv.writer(file)
			writer.writerow(['time', 'diff_T', 'abs_T'])

	current_time = time.time()

	if current_time - last_switch_time >= switch_interval:
		voltage = -voltage 
		dc205.set_voltage(voltage)
		last_switch_time = current_time

	ch1, ch2 = thermo.measure_both()
	diff_T = ch1
	abs_T = ch2

	#print(diff_T, abs_T)

	timestamp = time.time()
	t_dt    = datetime.now()
	with open(file_path, mode='a', newline='') as file:
		writer = csv.writer(file)
		writer.writerow([timestamp, diff_T, abs_T])

	try:
		conn.ping(reconnect=True, attempts=1, delay=0)
		insert_rtd(cur, t_dt, diff_T, abs_T)
	except mysql.connector.Error as e:
		try:
			if conn.is_connected():
				cur.close()
				conn.close()
			conn= mysql_connector.connect(host='192.168.1.2',user='writer',password='mossbauer_writer',database='slowcontrol')
			cur = conn.cursor()
			insert_rtd(cur, t_dt, diff_T, abs_T)
		except: 
			pass	
	

