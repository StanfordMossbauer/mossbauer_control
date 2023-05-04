import time
from mossbauer_control.motor import Motor

motor = Motor( agilent = "GPIB0::14::INSTR",arduino = "/dev/ttyACM0")

motor.velocity = -2
motor.start()
while motor.flagA==True:
     time.sleep(0.3)
motor.velocity = 0
motor.stop()
motor.close()

