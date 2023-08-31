import matplotlib.pylab as plt
import pandas as pd
import numpy as np

df = pd.read_csv("~/Data/20230512_scan/Fe0004_0.5_mms_0.01_mms_19in.dat", delimiter = '\t')
df2 = df.groupby(['nom_vel']).sum()
plt.errorbar(df2.index, 2*df2['count']/df2['seconds'],yerr= 2*np.sqrt(df2['count'])/df2['seconds'],fmt = 'k.')
plt.show()