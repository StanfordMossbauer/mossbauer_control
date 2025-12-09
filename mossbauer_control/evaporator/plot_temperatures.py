import numpy as np  
import matplotlib.pyplot as plt 

from matplotlib.animation import FuncAnimation
from statsmodels.tsa.api import SimpleExpSmoothing

## DEFINE CONSTANTS


num_thcoup = 10 # number of functioning thermocouples
delt_t = 0.5 * num_thcoup # read delay in seconds
sample_rate = 1000 * delt_t # read delay in milliseconds
sample_length = 30 * 60 # in seconds
num_samples = round (sample_length / delt_t) # number of samples in space

save_length = 10 # number of inputs saved for averaging
smoothing_param = 0.6 # parameter controlling exponential smoothing

time = np.linspace (0, sample_length - delt_t, num_samples) # shared time axis in seconds
fig, ax = plt.subplots (2) # instantiate the subplots

labels = ["T (V: 1-2)", "Manipulator (V: 1-2)", "Top Sphere (V: 3-4)", "Window L (V: 3-4)", "Window M (V: 5-6)", "Bottom Sphere (V: 5-6)", "Back Sphere (V: 5-6)", "Window S (V: 3-4)", "Reducer (V: 7)", "Window LL (V: 7)"]

f = open ("temperatures.txt", "r")
lns = f.readlines ()

temp_data = np.array ([ln.strip ().split (',')[1:-1] for ln in lns]).T.astype (np.float64) 
if temp_data.shape[1] > num_samples: temp_data = temp_data[:, -num_samples:]

change_data = np.array ([ln.strip ().split (',')[:-1] for ln in lns]).T.astype (np.float64) 
change_data = (change_data[1:, 1:] - change_data[1:, :-1]) / (change_data[0, 1:] - change_data[0, :-1]) * 60
change_data_mean = np.zeros ((num_thcoup, num_samples))
for i in range (len (change_data_mean[0])): change_data_mean[:, i] = change_data[:, i - num_samples - save_length:i - num_samples].mean (axis = 1)
if change_data.shape[1] > num_samples: change_data = change_data[:, -num_samples:]

## ANIMATE TEMPERATURE
temp_value_list = temp_data.copy ()
temp_line_values = [None] * num_thcoup
for i in range (num_thcoup): temp_line_values[i], = ax[0].plot ([], [], '.-', markersize = 0.5, label = f"{i + 1} {labels[i]}")
temp_data_list = temp_value_list.tolist ()

def temp_animate (i, num):
	with open ("temperatures.txt", "r") as file:
		value = float (file.readlines ()[-1].strip ().split (',')[1 + num])
	if not value: value = 0

	temp_data_list[num].append (value)
	temp_data_list[num].pop (0)

	temp_line_values[num].set_data (time, temp_data_list[num])
	return temp_line_values[num]

temp_anims = [None] * num_thcoup
for i in range (len (temp_anims)):
	temp_anims[i] = FuncAnimation (fig, temp_animate, fargs = (i,), interval = sample_rate, cache_frame_data = False)

## ANIMATE TEMPERATURE CHANGE
change_value_list = change_data.copy ()
change_value_mean_list = change_data_mean.copy ()
change_line_values = [None] * num_thcoup
change_line_means = [None] * num_thcoup
for i in range (num_thcoup):
	#change_line_values[i], = ax[1].plot ([], [], '.-', markersize = 0.5, label = f"{i + 1} {labels[i]}")
	change_line_means[i], = ax[1].plot ([], [], '.-', markersize = 0.5, label = f"{i + 1} {labels[i]}")
change_data_list = change_value_list.tolist ()
change_value_mean_list = change_value_mean_list.tolist ()
past_values = [[0]] * num_thcoup

def change_animate (i, num):
	with open ("temperatures.txt", "r") as file:
		lns = file.readlines ()[-2:]
		data = [np.array (ln.strip ().split (','))[[0, 1 + num]].astype (np.float64) for ln in lns]
		value = (data[1][1] - data[0][1]) / (data[1][0] - data[0][0]) * 60 # in C / min
	if not value: value = 0

	past_values[num] = past_values[num] + [value]
	if len (past_values[num]) > save_length: past_values[num].pop (0)

	change_value_mean = np.array (past_values[num]).mean ()
	#change_value_mean = SimpleExpSmoothing (past_values[num], initialization_method = "heuristic").fit (smoothing_level = smoothing_param, optimized = False).forecast ()[0]

	change_data_list[num].append (value)
	change_data_list[num].pop (0)
	change_value_mean_list[num].append (change_value_mean)
	change_value_mean_list[num].pop (0)

	
	#change_line_values[num].set_data (time, change_data_list[num])
	change_line_means[num].set_data (time, change_value_mean_list[num])
	#return change_line_values[num]
	return change_line_means[num]

change_anims = [None] * num_thcoup
for i in range (len (change_anims)):
	change_anims[i] = FuncAnimation (fig, change_animate, fargs = (i,), interval = sample_rate, cache_frame_data = False)

## FORMAT PLOT
ax[0].set_xlim (0, sample_length - delt_t)
ax[0].set_ylim (20, 200)

ax[0].set_title ("Temperature in Time")
ax[0].set_xlabel ("Time (seconds)")
ax[0].set_ylabel ("Temperature (C)")

ax[0].legend (loc = "upper left")

ax[1].set_xlim (0, sample_length - delt_t)
ax[1].set_ylim (-10, 10)

ax[1].set_title ("Mean Change in Temperature in Time")
ax[1].set_xlabel ("Time (seconds)")
ax[1].set_ylabel ("Change in Temperature (C / min)")

ax[1].plot (time, np.ones (len (time)) * 3, color = "black")
ax[1].plot (time, np.ones (len (time)) * -3, color = "black")

ax[1].legend (loc = "upper left")

plt.show ()