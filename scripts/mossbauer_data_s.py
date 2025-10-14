import pyvisa
import time 
import numpy as np
import csv 
import os
from pyvisa.constants import ControlFlow, Parity, StopBits
import pandas as pd
from datetime import datetime


import mysql.connector

from mossbauer_control.instruments import keithley
from mossbauer_control.instruments import SRS830

def insert_fast(cursor, t_dt, data_V, R, theta):
	cursor.execute(
		"INSERT INTO FAST (`time`, `VOLTMETER`, `SRS_R`,`SRS_THETA`) VALUES (%s, %s, %s)",
		(t_dt, float(data_V),float(R), float(theta))
	)

# Mysql connectors;
conn= mysql.connector.connect(host='192.168.2.2',user='writer',password='mossbauer_writer',database='slowcontrol')
cur=conn.cursor()




#when also measuring thermocouples
#thermo = keithley(gpib_address = 7)
voltmeter = keithley(gpib_address = 6)
srs = SRS830(gpib_address = 10)

#initialize SRS830
srs.reset()
srs.set_sensitivity(100) #added
results = []
time_const = 10
srs.set_time_constant(time_const)


#thermo.set_voltage_mode()
voltmeter.set_voltage_mode()
voltmeter.clear_buffer()
voltmeter.store_raw_readings()
voltmeter.cont_operation()
voltmeter.initialize()
#thermo.clear_buffer()
#thermo.store_raw_readings()
#thermo.cont_operation()
#thermo.initialize()
    
# data_V = []
# data_T = []
# data_theta = []
# data_amp = []
# timestamps = []
# start = time.time()

# i = 1
# while i<3:
#     i+=1
#     time.sleep(60)
#     data = voltmeter.get_data()
#     data_V.append(data)
#     data = thermo.get_data()
#     data_T.append(data)
#     timestamps.append(time.time())
#     R,theta, f_ref = srs.read_all()
#     data_amp.append(R)
#     data_theta.append(theta)

# df=pd.DataFrame(
#     {'time':timestamps,
#     'data V':data_V,
#     'data T': data_T,
#     'amp': data_amp,
#     'theta': data_theta}
#     )



# # Define the full file path
# save_path = r'C:\Users\mossbauer\Documents\data\0919\all_02.csv'
# os.makedirs(os.path.dirname(save_path), exist_ok=True)
# df.to_csv(save_path, index=False)


# save_path = r'C:\Users\mossbauer\Documents\data\0922\all_01.csv'
# os.makedirs(os.path.dirname(save_path), exist_ok=True)

# # Initialize file with header
# columns = ['time', 'data V', 'data T', 'amp', 'theta']
# df_empty = pd.DataFrame(columns=columns)
# df_empty.to_csv(save_path, index=False)

# i = 0
# while i < 3:
#     i += 1
#     time.sleep(60)

#     # Gather data
#     data_V = voltmeter.get_data()
#     data_T = thermo.get_data()
#     timestamp = time.time()
#     R, theta, f_ref = srs.read_all()

#     # Create one-row DataFrame
#     df_row = pd.DataFrame([[timestamp, data_V, data_T, R, theta]], columns=columns)

#     # Append to CSV
#     df_row.to_csv(save_path, mode='a', header=False, index=False)


#or we can create a new csv file every day
def get_file_path(base_dir):
    """Generate file path with current date"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"all_closed{date_str}.csv"
    return os.path.join(base_dir, filename)

# Folder to save CSVs
base_dir = r'C:\Users\mossbauer\Documents\data\1008'
os.makedirs(base_dir, exist_ok=True)

# Track current file date
current_day = datetime.now().date()
file_path = get_file_path(base_dir)

# Write header once per file
with open(file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    #writer.writerow(['time', 'data V', 'data T', 'amp', 'theta'])
    writer.writerow(['time', 'data V',  'amp', 'theta'])

while True:
    # Check if the date has changed
    now = datetime.now()
    if now.date() != current_day:
        # New day, create a new file
        current_day = now.date()
        file_path = get_file_path(base_dir)
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            #writer.writerow(['time', 'data V', 'data T', 'amp', 'theta'])
            writer.writerow(['time', 'data V',  'amp', 'theta'])

    # Sleep before getting data
    time.sleep(1)

    # Get data
    data_V = voltmeter.get_data()
    #data_T = thermo.get_data()
    timestamp = time.time()
    R, theta, f_ref = srs.read_all()

    # Write data to file
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        #writer.writerow([timestamp, data_V, data_T, R, theta])
        writer.writerow([timestamp, data_V, R, theta])


	try:
		conn.ping(reconnect=True, attempts=1, delay=0)
		insert_fast(cur, t_dt, diff_T, abs_T)
		conn.commit()
	except mysql.connector.Error as e:
		print("Connection Issues")
		try:
			if conn.is_connected():
				cur.close()
				conn.close()
			conn= mysql.connector.connect(host='192.168.2.2',user='writer',password='mossbauer_writer',database='slowcontrol')
			cur = conn.cursor()
			insert_fast(cur, t_dt, diff_T, abs_T)
			conn.commit()
		except: 
			pass	


