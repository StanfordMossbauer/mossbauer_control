from mossbauer_control.instruments import SRS860
from mossbauer_control.instruments import DS360
import time
import matplotlib.pyplot as plt

drive = DS360(gpib_address = 8)
srs = SRS860(gpib_address = 10)


drive.set_Vpp(20)
drive.set_frequency(200)
drive.output_on()


srs.experiment_setup()

flist = [20,40,100,140,170,200,230]
vpplist = [1,2,4,10,15,20,25,30,35]


fig, ax = plt.subplots(1,2)

for f in flist:
    r = []
    theta = []
    fout = []
    for vpp in vpplist:
        drive.set_frequency(f=f)
        drive.set_Vpp(vpp)
        time.sleep(1)
        out = srs.read_all()

        r.append(out[0])
        theta.append(out[1])
        fout.append(out[2])

    ax[0].plot(vpplist, r, label = "f = {f:3} Hz")
    ax[0].set_ylabel("R")
    ax[0].set_xlabel("Vpp")


    ax[1].plot(vpplist, theta, label = "f = {f:3} Hz")
    ax[1].set_ylabel("theta")
    ax[1].set_xlabel("Vpp")

plt.legend()
plt.show()
    


