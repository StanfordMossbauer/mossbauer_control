import time
from datetime import datetime

from mossbauer_control.instruments import DS360
from mossbauer_control.instruments import K263
from mossbauer_control.instruments import bnc555

# This script is used to set up parameters; 
import mysql.connector
# Mysql Connectors; 

drive = DS360(gpib_address = 8)
# Fast Stage function generator 

calibrator = K263(gpib_address = 9)
# Slow Stage function generator 

bnc = bnc555(gpib_address = 1)
# Camera Trigger;

# It is fine to write down the password here because 
# - The database is only accessible via LAN;
# - The writer could only read and "add" data to the database, could not delete; 
conn= mysql.connector.connect(host='192.168.2.2',user='writer',password='mossbauer_writer',database='slowcontrol')
cur=conn.cursor()

def insert_parameters(cursor, t_dt, f_f, f_A, s_c):
	cursor.execute("INSERT INTO parameters (`TIME`, `FAST_FREQUENCY`, \
     `FAST_AMPLITUDE`,`SLOW_CURRENT`) VALUES (%s, %s, %s, %s)",\
         (t_dt, float(f_f), float(f_A),float(s_c)))

def insert_data(conn,cursor,t_dt,f_f,f_A,s_c):
	try: 
		conn.ping(reconnect=True, attempts=1, delay=0)
		insert_parameters(cursor, t_dt, f_f, f_A, s_c)
		conn.commit()        
	except mysql.connector.Error as e:
		print("Connection Issues")
		try:
			if conn.is_connected():
				cur.close()
				conn.close()
			conn= mysql.connector.connect(host='192.168.2.2',user='writer',password='mossbauer_writer',database='slowcontrol')
			cur = conn.cursor()
			insert_parameters(cursor, t_dt, f_f, f_A, s_c)
			conn.commit()
		except: 
			pass	 
	return 

#set up fast stage
amp = 6.579
freq= 30 
current=1E-9

offset_V = amp/2
drive.set_sine()
drive.set_frequency(freq)
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
    calibrator.set_current(current)
    t_t=datetime.now()
    insert_data(conn,cur,t_t,freq,amp,current)
    #dc205.set_voltage(2)
    time.sleep(500)
    
    t_t=datetime.now()
    calibrator.set_current(-1*current)
    insert_data(conn,cur,t_t,freq,amp,-1*current)
    #dc205.set_voltage(-2)
    time.sleep(500)
      
    i+=1
calibrator.stop()
#dc205.close()






