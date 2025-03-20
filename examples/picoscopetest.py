from mossbauer_control.instruments import PS2000
import matplotlib.pyplot as plt
import numpy as np

ps = PS2000()

print(ps.getUnitInfo(1))

#ps.setup_mossbauer_scan()
ps.setChannel(channel='A', coupling='DC', VRange=10, VOffset=0.0, enabled=True)
ps.setChannel(channel='B', coupling='DC', VRange=10, VOffset=0.0, enabled=True)

si = ps.setSamplingInterval(5e-3,10)

ps.setSimpleTrigger(trigSrc="B",threshold_V= 1.0,direction="Rising",delay=0,enabled=True,timeout_ms=100000)   
ps.runBlock()

ps.waitReady()

t = np.arange(0,si[1])*si[0]
dataA = ps.getDataV("A")
dataB = ps.getDataV("B")
plt.plot(t,dataA)
plt.plot(t,dataB)

plt.show()

#ps.close()