

from yoctopuce.yocto_api import *
from yoctopuce.yocto_temperature import *
from yoctopuce.yocto_humidity import *
from yoctopuce.yocto_pressure import *
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import csv




class Yoctopuce:
	def __init__(self, address):

		errmsg = YRefParam()
		if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
			#sys.exit("init error :" + errmsg.value)
			print("error :" + errmsg.value)

		print(address)
		
		self.temperature = YTemperature.FindTemperature(address +'.temperature')
		self.humidity = YHumidity.FindHumidity(address+'.humidity')
		self.pressure = YPressure.FindPressure(address+'.pressure')

	def __del__(self):
		print("Closing yoctopuce")

        #if YAPI.RegisterHub("127.0.0.1", errmsg) != YAPI.SUCCESS:
            # use YAPI.RegisterHub("127.0.0.1", errmsg) if dev is connected to the same pc
            # if this failed, try YAPI.RegisterHub("usb", errmsg)



            
        


if __name__=='__main__':
	address = 'METEOMK2-2377A2'
	yct1= Yoctopuce(address)

# 	T_list = []
# 	P_list = []
# 	H_list = []
# 	timestamps = []
# 	start = time.time()
# 	i=1
# 	while True:
# 		i+=1
# 		time.sleep(1)
# 		T_list.append(yct1.temperature.get_currentValue())
# 		H_list.append(yct1.humidity.get_currentValue())
# 		P_list.append(yct1.pressure.get_currentValue())
# 		timestamps.append(time.time()-start)

# 	df=pd.DataFrame(
# 		{'time':timestamps,
# 		'T':T_list,
# 		'P':P_list,
# 		'H':H_list}
# 		)

# 	# Define the full file path
# 	save_path = r'C:\Users\mossbauer\Documents\data\gpib-isolator_0620\test_keithley_straingauge_nocurrentsource_2_yocto.csv'
# 	os.makedirs(os.path.dirname(save_path), exist_ok=True)
# 	df.to_csv(save_path, index=False)



# # Base save directory
# base_dir = r'C:\Users\mossbauer\Documents\data\1008'
# os.makedirs(base_dir, exist_ok=True)

# # Start time
# start = time.time()

# # Helper function to generate filename for the current date
# def get_filename():
#     date_str = datetime.now().strftime('%Y-%m-%d')
#     return os.path.join(base_dir, f'{date_str}_yocto_data.csv')

# # Initial filename and file setup
# current_date = datetime.now().date()
# file_path = get_filename()
# file = open(file_path, 'a')

# # Write header if file is new
# if os.stat(file_path).st_size == 0:
#     file.write('time,T,P,H\n')

# print(f"Logging to: {file_path}")

# try:
#     while True:
#         time.sleep(1)
#         now = datetime.now()
#         new_date = now.date()

#         # Check if date has changed
#         if new_date != current_date:
#             file.close()
#             current_date = new_date
#             file_path = get_filename()
#             file = open(file_path, 'a')
#             file.write('time,T,P,H\n')  # new file = write header
#             print(f"Date changed. Logging to new file: {file_path}")

#         current_time = time.time() - start
#         T = yct1.temperature.get_currentValue()
#         H = yct1.humidity.get_currentValue()
#         P = yct1.pressure.get_currentValue()

#         # Write new row
# 		with open(file_path, mode='a', newline='') as file:
#         	writer = csv.writer(file)
#         	#writer.writerow([timestamp, data_V, data_T, R, theta])
#         	writer.writerow([timestamp, T, H, P])


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
    writer.writerow(['time', 'T',  'H', 'P'])

while True:
    # Check if the date has changed
    now = datetime.now()
    if now.date() != current_day:
        # New day, create a new file
        current_day = now.date()
        file_path = get_file_path(base_dir)
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['time', 'T', 'H', 'P'])

    # Sleep before getting data
    time.sleep(1)

    # Get data
    timestamp = time.time()
    T = yct1.temperature.get_currentValue()
    H = yct1.humidity.get_currentValue()
    P = yct1.pressure.get_currentValue()

    # Write data to file
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, T, H, P])