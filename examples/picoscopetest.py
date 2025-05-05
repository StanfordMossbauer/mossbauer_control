from mossbauer_control.instruments import PS4000
import matplotlib.pyplot as plt
import numpy as np
import json

ps = PS4000()

channels = ["A", "B"]
#channels = ["A"]
vrange = [0, 0.01] #set in V
#print(ps.getUnitInfo(4))

for i, ch in enumerate(channels):
    ps.setChannel(channel=ch, coupling='AC', VRange=vrange[i], VOffset=0.0, enabled=True) #set to AC for the voltage source

si = ps.setSamplingInterval(1/20e3,400)    #sampling rate, number of points
ps.memorySegments(1)
ps.setNoOfCaptures(1)

#ps.setSimpleTrigger(trigSrc="B",threshold_V= 1.0,direction="Rising",delay=0,enabled=True,timeout_ms=100000)   
ps.runBlock()
ps.waitReady()


#dataA = ps.getDataV("A")

dataA, nSamps, ovf  = ps.getDataRawBulkOld(["A"])
dataB, nSamps, ovf = ps.getDataRawBulkOld(["B"])
#print("Channel A Data: ", dataA)
#print("Channel B Data: ", dataB)
#plt.figure()
#plt.plot(dataA)
#plt.figure()
#plt.plot(dataB)


#for ch in channels:
#    (data, nSamps, ovf) = ps.getDataRawBulkOld(ch)
#print('channels', channels)
#print(data)
ps.close()



directory = 'C:\\Users\\Mossbauer\\Documents\\data\\20250424_SRSDS2360_noise\\'
filename = directory+ "400s_DC_0V_03.bin"
filenameA= directory + "400s_DC_0V_03A.bin"
filenameB= directory + "400s_DC_0V_03B.bin"
saveFileA = open(filenameA, 'wb')
saveFileB = open(filenameB, 'wb')

dataA.T.tofile(saveFileA)
dataB.T.tofile(saveFileB)


params = {
            'directory': directory,
            'filenameA':filenameA,
            'filenameB':filenameB,
            'filename':filename,
            'sampling_interval' : si[0],
            'sampling_time' : si[0]*si[1],
            'channels' : channels,
            'vrange' : vrange,
            'bitresolution': 16,
            'description': "this measurement..."
}

jfile = filename[:-4] + '.json'
with open(jfile, 'w') as outfile:
        json.dump(params, outfile, indent=4)




### DATA CAN BE READ AS:
#with open(jfile) as f:   #or put path here
#    params = json.load(f)
#data  = np.fromfile(params['filenameA'],dtype=np.int16).reshape(-1,len(params['channels'])).T
#data  = np.fromfile(jfile, dtype=np.int16).reshape(-1,len(params['channels'])).T

#t = np.arange(0,len(data[0]))*params['sampling_interval']
#data_A_V = data[0]*vrange[0]/2**(params['bitresolution']-1) 
#data_B_V = data[1]*vrange[1]/2**(params['bitresolution']-1) 
#plt.figure()
#plt.plot(t,data_A_V) #mV
#plt.figure()
#plt.plot(t, data_B_V) #mV 
#plt.show()
