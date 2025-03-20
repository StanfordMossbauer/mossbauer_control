import numpy as np
import matplotlib.pyplot as plt
import os

hlist = []
dlist = []
directory = '/home/mossbauer/Data/20231004_scan/'

for file in sorted(os.listdir(directory)):
	if file.split("_")[-3]=='avghist':
		#d = float(file.split("_")[-1][:-6])
		d= 1
		dlist.append(d)
		
		h = np.loadtxt(directory+file)
		hlist.append(h)
		plt.plot(h, label = 'd = {} inches'.format(d))
		print(d)



